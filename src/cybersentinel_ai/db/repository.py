from datetime import UTC, datetime

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import (
    DetectionEventCreate,
    IncidentCreate,
    IncidentTimelineCreate,
    IncidentUpdate,
)
from cybersentinel_ai.db.models import (
    Asset,
    DetectionEvent,
    Incident,
    IncidentAsset,
    IncidentDetection,
    IncidentTimeline,
    ResponseAction,
)


def event_visibility(user_id: int, role: str):
    if role == "ADMIN":
        return None
    return or_(
        DetectionEvent.workspace == "DEMO",
        and_(
            DetectionEvent.owner_user_id == user_id,
            or_(
                DetectionEvent.sandbox_expires_at.is_(None),
                DetectionEvent.sandbox_expires_at > datetime.now(UTC),
            ),
        ),
    )


def incident_visibility(user_id: int, role: str):
    if role == "ADMIN":
        return None
    return or_(
        Incident.workspace == "DEMO",
        and_(
            Incident.owner_user_id == user_id,
            or_(
                Incident.sandbox_expires_at.is_(None),
                Incident.sandbox_expires_at > datetime.now(UTC),
            ),
        ),
    )


def create_detection_event(
    database: Session,
    payload: DetectionEventCreate,
    *,
    idempotency_key: str | None = None,
    workspace: str = "DEMO",
    owner_user_id: int | None = None,
    sandbox_expires_at: datetime | None = None,
    commit: bool = True,
) -> DetectionEvent:
    event = DetectionEvent(
        **payload.model_dump(),
        idempotency_key=idempotency_key,
        workspace=workspace,
        owner_user_id=owner_user_id,
        sandbox_expires_at=sandbox_expires_at,
    )

    database.add(event)
    if commit:
        database.commit()
    else:
        database.flush()
    database.refresh(event)

    return event


def get_detection_event(
    database: Session,
    event_id: int,
    *,
    user_id: int | None = None,
    role: str | None = None,
) -> DetectionEvent | None:
    statement = select(DetectionEvent).where(DetectionEvent.id == event_id)
    if user_id is not None and role != "ADMIN":
        statement = statement.where(event_visibility(user_id, role or "VIEWER"))
    return database.scalar(statement)


def get_detection_event_by_idempotency_key(
    database: Session,
    idempotency_key: str,
) -> DetectionEvent | None:
    return database.scalar(
        select(DetectionEvent).where(
            DetectionEvent.idempotency_key == idempotency_key
        )
    )


def list_detection_events(
    database: Session,
    limit: int = 100,
    offset: int = 0,
    user_id: int | None = None,
    role: str | None = None,
) -> list[DetectionEvent]:
    statement = (
        select(DetectionEvent)
        .where(
            *(
                ()
                if user_id is None or role == "ADMIN"
                else (
                    event_visibility(user_id, role or "VIEWER"),
                )
            )
        )
        .order_by(DetectionEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    return list(database.scalars(statement).all())


def search_detection_events(
    database: Session,
    *,
    limit: int = 25,
    offset: int = 0,
    severity: str | None = None,
    attack_type: str | None = None,
    source_ip: str | None = None,
    min_risk: float | None = None,
    max_risk: float | None = None,
    query: str | None = None,
    user_id: int | None = None,
    role: str | None = None,
) -> tuple[list[DetectionEvent], int]:
    filters = []

    if user_id is not None and role != "ADMIN":
        filters.append(event_visibility(user_id, role or "VIEWER"))

    if severity:
        filters.append(
            func.upper(DetectionEvent.severity) == severity.upper()
        )

    if attack_type:
        filters.append(
            DetectionEvent.predicted_label.ilike(f"%{attack_type}%")
        )

    if source_ip:
        filters.append(
            DetectionEvent.source_ip.ilike(f"%{source_ip}%")
        )

    if min_risk is not None:
        filters.append(DetectionEvent.risk_score >= min_risk)

    if max_risk is not None:
        filters.append(DetectionEvent.risk_score <= max_risk)

    if query:
        pattern = f"%{query.strip()}%"
        filters.append(
            or_(
                DetectionEvent.predicted_label.ilike(pattern),
                DetectionEvent.source_ip.ilike(pattern),
                DetectionEvent.destination_ip.ilike(pattern),
                DetectionEvent.hostname.ilike(pattern),
                DetectionEvent.asset_id.ilike(pattern),
                DetectionEvent.ioc_value.ilike(pattern),
                DetectionEvent.external_id.ilike(pattern),
            )
        )

    count_statement = (
        select(func.count())
        .select_from(DetectionEvent)
        .where(*filters)
    )

    total = int(database.scalar(count_statement) or 0)

    statement = (
        select(DetectionEvent)
        .where(*filters)
        .order_by(DetectionEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    items = list(database.scalars(statement).all())

    return items, total


def create_incident(
    database: Session,
    payload: IncidentCreate,
    workspace: str = "DEMO",
    owner_user_id: int | None = None,
    sandbox_expires_at: datetime | None = None,
    *,
    commit: bool = True,
) -> Incident:
    incident = Incident(
        **payload.model_dump(),
        workspace=workspace,
        owner_user_id=owner_user_id,
        sandbox_expires_at=sandbox_expires_at,
    )

    database.add(incident)
    database.flush()
    incident.display_id = f"CS-{incident.created_at.year}-{incident.id:04d}"
    incident.first_seen_at = (
        incident.detection_event.occurred_at
        if incident.detection_event and incident.detection_event.occurred_at
        else incident.created_at
    )
    incident.last_event_at = incident.first_seen_at

    timeline = IncidentTimeline(
        incident_id=incident.id,
        action="INCIDENT_CREATED",
        description="Incident created",
    )

    database.add(timeline)

    if incident.detection_event_id:
        database.add(
            IncidentDetection(
                incident_id=incident.id,
                detection_event_id=incident.detection_event_id,
            )
        )
        if incident.detection_event and incident.detection_event.asset_id:
            asset = database.get(Asset, incident.detection_event.asset_id)
            if asset is not None:
                database.add(
                    IncidentAsset(incident_id=incident.id, asset_id=asset.id)
                )
        detection_timeline = IncidentTimeline(
            incident_id=incident.id,
            action="DETECTION_RECEIVED",
            description=(
                f"Linked detection event {incident.detection_event_id} "
                "to incident"
            ),
        )

        database.add(detection_timeline)

    if commit:
        database.commit()
    else:
        database.flush()
    database.refresh(incident)

    return incident


def _incident_filters(
    *,
    user_id: int | None = None,
    role: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    priority: str | None = None,
    assignee_user_id: int | None = None,
    asset_id: str | None = None,
    attack_type: str | None = None,
    source_ip: str | None = None,
    query: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list:
    filters = []
    if user_id is not None and role != "ADMIN":
        filters.append(incident_visibility(user_id, role or "VIEWER"))
    if status:
        filters.append(Incident.status == status.upper())
    if severity:
        filters.append(Incident.severity == severity.upper())
    if priority:
        filters.append(Incident.priority == priority.upper())
    if assignee_user_id is not None:
        filters.append(Incident.assignee_user_id == assignee_user_id)
    if since is not None:
        filters.append(Incident.created_at >= since)
    if until is not None:
        filters.append(Incident.created_at <= until)
    if asset_id:
        filters.append(
            Incident.id.in_(
                select(IncidentAsset.incident_id).where(
                    IncidentAsset.asset_id == asset_id
                )
            )
        )
    if attack_type or source_ip:
        detection_filters = []
        if attack_type:
            detection_filters.append(
                DetectionEvent.predicted_label.ilike(f"%{attack_type}%")
            )
        if source_ip:
            detection_filters.append(DetectionEvent.source_ip.ilike(f"%{source_ip}%"))
        filters.append(
            Incident.id.in_(
                select(IncidentDetection.incident_id)
                .join(
                    DetectionEvent,
                    DetectionEvent.id == IncidentDetection.detection_event_id,
                )
                .where(*detection_filters)
            )
        )
    if query:
        pattern = f"%{query.strip()}%"
        filters.append(
            or_(
                Incident.display_id.ilike(pattern),
                Incident.title.ilike(pattern),
                Incident.description.ilike(pattern),
                Incident.correlation_key.ilike(pattern),
                Incident.resolution_reason.ilike(pattern),
            )
        )
    return filters


def list_incidents(
    database: Session,
    *,
    limit: int = 25,
    offset: int = 0,
    user_id: int | None = None,
    role: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    priority: str | None = None,
    assignee_user_id: int | None = None,
    asset_id: str | None = None,
    attack_type: str | None = None,
    source_ip: str | None = None,
    query: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> tuple[list[Incident], int]:
    filters = _incident_filters(
        user_id=user_id,
        role=role,
        status=status,
        severity=severity,
        priority=priority,
        assignee_user_id=assignee_user_id,
        asset_id=asset_id,
        attack_type=attack_type,
        source_ip=source_ip,
        query=query,
        since=since,
        until=until,
    )
    count_statement = (
        select(func.count())
        .select_from(Incident)
        .where(*filters)
    )

    total = int(database.scalar(count_statement) or 0)

    statement = (
        select(Incident)
        .where(*filters)
        .order_by(Incident.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    items = list(database.scalars(statement).all())

    return items, total


def summarize_incidents(
    database: Session,
    *,
    user_id: int | None = None,
    role: str | None = None,
    severity: str | None = None,
    priority: str | None = None,
    assignee_user_id: int | None = None,
    asset_id: str | None = None,
    attack_type: str | None = None,
    source_ip: str | None = None,
    query: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> dict[str, int | dict[str, int]]:
    filters = _incident_filters(
        user_id=user_id,
        role=role,
        severity=severity,
        priority=priority,
        assignee_user_id=assignee_user_id,
        asset_id=asset_id,
        attack_type=attack_type,
        source_ip=source_ip,
        query=query,
        since=since,
        until=until,
    )
    statuses = ("OPEN", "INVESTIGATING", "IN_PROGRESS", "CONTAINED", "RESOLVED")
    rows = database.execute(
        select(Incident.status, func.count(Incident.id))
        .where(*filters)
        .group_by(Incident.status)
    ).all()
    by_status = {status: 0 for status in statuses}
    for status, count in rows:
        by_status[str(status).upper()] = int(count)
    active = sum(by_status[status] for status in statuses[:-1])
    return {
        "total": sum(by_status.values()),
        "active": active,
        "by_status": by_status,
    }


def get_incident(
    database: Session,
    incident_id: int,
    *,
    user_id: int | None = None,
    role: str | None = None,
) -> Incident | None:
    statement = select(Incident).where(Incident.id == incident_id)
    if user_id is not None and role != "ADMIN":
        statement = statement.where(incident_visibility(user_id, role or "VIEWER"))
    return database.scalar(statement)


def reset_user_sandbox(database: Session, user_id: int) -> tuple[int, int]:
    incident_ids = list(
        database.scalars(
            select(Incident.id).where(
                Incident.workspace == "SANDBOX", Incident.owner_user_id == user_id
            )
        )
    )
    if incident_ids:
        database.execute(
            delete(ResponseAction).where(ResponseAction.incident_id.in_(incident_ids))
        )
        database.execute(
            delete(IncidentAsset).where(IncidentAsset.incident_id.in_(incident_ids))
        )
        database.execute(
            delete(IncidentDetection).where(
                IncidentDetection.incident_id.in_(incident_ids)
            )
        )
        database.execute(
            delete(IncidentTimeline).where(IncidentTimeline.incident_id.in_(incident_ids))
        )
        database.execute(delete(Incident).where(Incident.id.in_(incident_ids)))
    event_result = database.execute(
        delete(DetectionEvent).where(
            DetectionEvent.workspace == "SANDBOX",
            DetectionEvent.owner_user_id == user_id,
        )
    )
    return int(event_result.rowcount or 0), len(incident_ids)


def purge_expired_sandboxes(database: Session) -> int:
    expired_event_ids = list(
        database.scalars(
            select(DetectionEvent.id).where(
                DetectionEvent.workspace == "SANDBOX",
                DetectionEvent.sandbox_expires_at <= datetime.now(UTC),
            )
        )
    )
    if not expired_event_ids:
        return 0
    incident_ids = list(
        database.scalars(
            select(Incident.id).where(
                Incident.workspace == "SANDBOX",
                Incident.detection_event_id.in_(expired_event_ids),
            )
        )
    )
    if incident_ids:
        database.execute(
            delete(ResponseAction).where(ResponseAction.incident_id.in_(incident_ids))
        )
        database.execute(
            delete(IncidentAsset).where(IncidentAsset.incident_id.in_(incident_ids))
        )
        database.execute(
            delete(IncidentDetection).where(
                IncidentDetection.incident_id.in_(incident_ids)
            )
        )
        database.execute(
            delete(IncidentTimeline).where(IncidentTimeline.incident_id.in_(incident_ids))
        )
        database.execute(delete(Incident).where(Incident.id.in_(incident_ids)))
    database.execute(delete(DetectionEvent).where(DetectionEvent.id.in_(expired_event_ids)))
    return len(expired_event_ids)


def update_incident_status(
    database: Session,
    incident_id: int,
    payload: IncidentUpdate,
    *,
    commit: bool = True,
) -> Incident | None:
    incident = database.get(Incident, incident_id)

    if incident is None:
        return None

    changes = payload.model_dump(exclude_unset=True)
    descriptions = []
    changed_fields: set[str] = set()
    for field, value in changes.items():
        old_value = getattr(incident, field)
        if old_value == value:
            continue
        setattr(incident, field, value)
        changed_fields.add(field)
        descriptions.append(f"{field} changed from {old_value!r} to {value!r}")

    if payload.status == "RESOLVED":
        incident.resolved_at = datetime.now(UTC)
    elif payload.status is not None and incident.status != "RESOLVED":
        incident.resolved_at = None

    timeline = IncidentTimeline(
        incident_id=incident_id,
        action="STATUS_CHANGE" if "status" in changed_fields else "CASE_UPDATED",
        description="; ".join(descriptions) or "Case update requested with no changes",
    )

    database.add(timeline)

    if commit:
        database.commit()
    else:
        database.flush()
    database.refresh(incident)

    return incident


def create_incident_timeline(
    database: Session,
    incident_id: int,
    payload: IncidentTimelineCreate,
    *,
    commit: bool = True,
) -> IncidentTimeline:
    timeline = IncidentTimeline(
        incident_id=incident_id,
        **payload.model_dump(),
    )

    database.add(timeline)
    if commit:
        database.commit()
    else:
        database.flush()
    database.refresh(timeline)

    return timeline


def list_incident_timelines(
    database: Session,
    incident_id: int,
) -> list[IncidentTimeline]:
    statement = (
        select(IncidentTimeline)
        .where(IncidentTimeline.incident_id == incident_id)
        .order_by(IncidentTimeline.created_at.desc())
    )

    return list(database.scalars(statement).all())
