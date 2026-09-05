from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import IngestionEventCreate
from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.models import (
    AlertRule,
    DetectionEvent,
    Incident,
    IncidentDetection,
    IncidentTimeline,
    IngestionJob,
    NotificationDelivery,
)

SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def ingestion_key(source_type: str, external_id: str) -> str:
    value = f"{source_type.strip().lower()}:{external_id.strip()}"
    return sha256(value.encode("utf-8")).hexdigest()


def create_ingestion_job(
    database: Session,
    payload: IngestionEventCreate,
    *,
    max_attempts: int,
) -> tuple[IngestionJob, bool]:
    key = ingestion_key(payload.source_type, payload.external_id)
    existing = database.scalar(
        select(IngestionJob).where(IngestionJob.idempotency_key == key)
    )
    if existing is not None:
        return existing, True

    job = IngestionJob(
        idempotency_key=key,
        source_type=payload.source_type,
        external_id=payload.external_id,
        payload=payload.model_dump(mode="json"),
        max_attempts=max_attempts,
    )
    database.add(job)
    database.flush()
    return job, False


def _matches(rule: AlertRule, event: DetectionEvent) -> bool:
    if not rule.enabled or event.risk_score < rule.min_risk_score:
        return False
    severities = {item for item in rule.severities.upper().split(",") if item}
    if severities and event.severity.upper() not in severities:
        return False
    if rule.require_review and not event.requires_review:
        return False
    return not rule.label_pattern or rule.label_pattern.lower() in event.predicted_label.lower()


def _derive_correlation_key(payload: IngestionEventCreate) -> str:
    if payload.correlation_key:
        return payload.correlation_key
    asset = (
        payload.asset_id
        or payload.hostname
        or payload.destination_ip
        or payload.source_ip
        or "unknown"
    )
    return f"{asset.lower()}:{payload.predicted_label.lower()}"[:255]


def _correlate_incident(
    database: Session,
    event: DetectionEvent,
    *,
    window_minutes: int,
) -> Incident:
    occurred_at = _as_utc(event.occurred_at or event.created_at)
    cutoff = occurred_at - timedelta(minutes=window_minutes)
    incident = database.scalar(
        select(Incident)
        .where(
            Incident.correlation_key == event.correlation_key,
            Incident.status.in_(("OPEN", "IN_PROGRESS")),
            or_(Incident.last_event_at.is_(None), Incident.last_event_at >= cutoff),
        )
        .order_by(Incident.created_at.desc())
        .with_for_update(of=Incident)
    )
    if incident is None:
        incident = Incident(
            title=f"{event.predicted_label} correlated activity",
            severity=event.severity.upper(),
            status="OPEN",
            description=(
                f"Correlated from {event.source_type or 'security'} event "
                f"{event.external_id or event.id}"
            ),
            detection_event_id=event.id,
            correlation_key=event.correlation_key,
            event_count=1,
            last_event_at=occurred_at,
        )
        database.add(incident)
        database.flush()
        database.add_all(
            [
                IncidentTimeline(
                    incident_id=incident.id,
                    action="INCIDENT_CREATED",
                    description="Incident created by configured alert rule",
                ),
                IncidentTimeline(
                    incident_id=incident.id,
                    action="DETECTION_CORRELATED",
                    description=f"Linked detection event {event.id} to incident",
                ),
            ]
        )
    else:
        incident.event_count += 1
        previous_event_at = _as_utc(incident.last_event_at or occurred_at)
        incident.last_event_at = max(previous_event_at, occurred_at)
        if SEVERITY_RANK.get(event.severity.upper(), 0) > SEVERITY_RANK.get(
            incident.severity.upper(), 0
        ):
            incident.severity = event.severity.upper()
        database.add(
            IncidentTimeline(
                incident_id=incident.id,
                action="DETECTION_CORRELATED",
                description=f"Correlated detection event {event.id} into incident",
            )
        )

    database.add(
        IncidentDetection(incident_id=incident.id, detection_event_id=event.id)
    )
    database.flush()
    return incident


def process_ingestion_job(database: Session, job_id: int) -> dict[str, int | str | None]:
    job = database.scalar(
        select(IngestionJob).where(IngestionJob.id == job_id).with_for_update()
    )
    if job is None:
        raise LookupError(f"ingestion job {job_id} not found")
    if job.status == "COMPLETED":
        return {"job_id": job.id, "event_id": job.detection_event_id, "status": job.status}

    payload = IngestionEventCreate.model_validate(job.payload)
    event = database.scalar(
        select(DetectionEvent).where(DetectionEvent.idempotency_key == job.idempotency_key)
    )
    if event is None:
        event_data = payload.model_dump(
            exclude={"external_id", "source_type", "occurred_at", "correlation_key"}
        )
        event = DetectionEvent(
            **event_data,
            external_id=payload.external_id,
            source_type=payload.source_type,
            idempotency_key=job.idempotency_key,
            occurred_at=payload.occurred_at or datetime.now(UTC),
            correlation_key=_derive_correlation_key(payload),
        )
        database.add(event)
        database.flush()

    rules = list(
        database.scalars(
            select(AlertRule)
            .where(AlertRule.enabled.is_(True))
            .order_by(AlertRule.priority.asc(), AlertRule.id.asc())
        ).all()
    )
    matched = [rule for rule in rules if _matches(rule, event)]
    incident = None
    if any(rule.auto_create_incident for rule in matched):
        incident = _correlate_incident(
            database,
            event,
            window_minutes=get_settings().correlation_window_minutes,
        )

    channels = {
        channel
        for rule in matched
        for channel in rule.notification_channels.lower().split(",")
        if channel
    }
    for channel in sorted(channels):
        exists = database.scalar(
            select(NotificationDelivery.id).where(
                NotificationDelivery.detection_event_id == event.id,
                NotificationDelivery.channel == channel,
            )
        )
        if exists is None:
            database.add(
                NotificationDelivery(
                    detection_event_id=event.id,
                    incident_id=incident.id if incident else None,
                    channel=channel,
                    max_attempts=get_settings().ingestion_max_attempts,
                )
            )

    job.status = "COMPLETED"
    job.detection_event_id = event.id
    job.last_error = None
    job.next_retry_at = None
    log_action(
        database,
        None,
        "INGEST_SECURITY_EVENT",
        f"Processed {payload.source_type} event {payload.external_id}",
        "DETECTION_EVENT",
        event.id,
        commit=False,
    )
    database.flush()
    return {
        "job_id": job.id,
        "event_id": event.id,
        "incident_id": incident.id if incident else None,
        "status": job.status,
    }


def mark_job_failed(database: Session, job_id: int, error: Exception) -> str:
    job = database.get(IngestionJob, job_id)
    if job is None:
        return "MISSING"
    job.attempts += 1
    job.last_error = str(error)[:2000]
    if job.attempts >= job.max_attempts:
        job.status = "DEAD_LETTER"
        job.next_retry_at = None
    else:
        job.status = "RETRY"
        delay = min(300, 2 ** job.attempts)
        job.next_retry_at = datetime.now(UTC) + timedelta(seconds=delay)
    database.commit()
    return job.status


def next_due_jobs(database: Session, limit: int = 100) -> list[int]:
    now = datetime.now(UTC)
    return list(
        database.scalars(
            select(IngestionJob.id)
            .where(
                IngestionJob.status.in_(("PENDING", "RETRY")),
                or_(IngestionJob.next_retry_at.is_(None), IngestionJob.next_retry_at <= now),
            )
            .order_by(IngestionJob.received_at.asc())
            .limit(limit)
        ).all()
    )
