from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import (
    DetectionEventCreate,
    DetectionEventPage,
    DetectionEventRead,
    IncidentCreate,
    SandboxSimulationCreate,
    SandboxSimulationRead,
)
from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.core.config import Settings, get_settings
from cybersentinel_ai.db.database import atomic, get_db
from cybersentinel_ai.db.models import DetectionEvent
from cybersentinel_ai.db.repository import (
    create_detection_event,
    create_incident,
    get_detection_event,
    get_detection_event_by_idempotency_key,
    list_detection_events,
    purge_expired_sandboxes,
    reset_user_sandbox,
    search_detection_events,
)
from cybersentinel_ai.security.dependencies import get_current_user
from cybersentinel_ai.security.rbac import UserRole, require_role

router = APIRouter(prefix="/events", tags=["Detection Events"])

DatabaseSession = Annotated[Session, Depends(get_db)]

SIMULATION_PRESETS = {
    "RANSOMWARE": ("198.51.100.23", 0.99, 0.96, 1.0, 98.0, "CRITICAL", 443),
    "SSH-BRUTE-FORCE": ("203.0.113.44", 0.91, 0.76, 0.9, 88.0, "HIGH", 22),
    "PORT-SCAN": ("198.51.100.77", 0.74, 0.72, 0.75, 68.0, "MEDIUM", 22),
    "PHISHING": ("192.0.2.36", 0.82, 0.58, 0.7, 72.0, "MEDIUM", 443),
    "DATA-EXFILTRATION": ("203.0.113.109", 0.97, 0.91, 0.95, 94.0, "CRITICAL", 443),
}


@router.post("", response_model=DetectionEventRead, status_code=201)
def create_event(
    payload: DetectionEventCreate,
    database: DatabaseSession,
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", min_length=1, max_length=128),
    ] = None,
    current_user=Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.SENIOR_ANALYST,
            UserRole.ANALYST,
        )
    ),
    settings: Settings = Depends(get_settings),
) -> DetectionEventRead:
    if idempotency_key:
        existing = get_detection_event_by_idempotency_key(
            database,
            idempotency_key,
        )
        if existing is not None:
            return existing

    try:
        expires_at = datetime.now(UTC) + timedelta(hours=settings.sandbox_ttl_hours)
        with atomic(database):
            event = create_detection_event(
                database,
                payload,
                idempotency_key=idempotency_key,
                workspace="SANDBOX",
                owner_user_id=current_user.id,
                sandbox_expires_at=expires_at,
                commit=False,
            )

            log_action(
                database,
                current_user.id,
                "CREATE_DETECTION_EVENT",
                f"Created detection event {event.id}",
                "DETECTION_EVENT",
                event.id,
                commit=False,
            )

            threshold = get_settings().auto_incident_risk_threshold

            if event.requires_review and event.risk_score >= threshold:
                incident = create_incident(
                    database,
                    IncidentCreate(
                        title=f"{event.predicted_label} detection",
                        severity=event.severity,
                        status="OPEN",
                        description=(
                            f"Automatically created from detection event {event.id} "
                            f"with risk score {event.risk_score:.1f}"
                        ),
                        detection_event_id=event.id,
                    ),
                    workspace="SANDBOX",
                    owner_user_id=current_user.id,
                    sandbox_expires_at=expires_at,
                    commit=False,
                )

                log_action(
                    database,
                    None,
                    "CREATE_INCIDENT_FROM_DETECTION",
                    (
                        f"Automatically created incident {incident.id} "
                        f"from detection event {event.id}"
                    ),
                    "INCIDENT",
                    incident.id,
                    commit=False,
                )
    except IntegrityError:
        if not idempotency_key:
            raise

        existing = get_detection_event_by_idempotency_key(
            database,
            idempotency_key,
        )
        if existing is None:
            raise

        return existing

    return event


@router.post("/simulate", response_model=SandboxSimulationRead, status_code=201)
def simulate_event(
    payload: SandboxSimulationCreate,
    database: DatabaseSession,
    current_user=Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> SandboxSimulationRead:
    now = datetime.now(UTC)
    with atomic(database):
        purge_expired_sandboxes(database)
        current_count = database.scalar(
            select(func.count())
            .select_from(DetectionEvent)
            .where(
                DetectionEvent.workspace == "SANDBOX",
                DetectionEvent.owner_user_id == current_user.id,
            )
        ) or 0
        if current_count >= settings.sandbox_max_events_per_user:
            raise HTTPException(
                status_code=429,
                detail="Sandbox event limit reached. Reset your sandbox to continue.",
            )

        (
            default_source,
            confidence,
            anomaly,
            rule_score,
            risk,
            severity,
            port,
        ) = SIMULATION_PRESETS[payload.scenario]
        expires_at = now + timedelta(hours=settings.sandbox_ttl_hours)
        event = create_detection_event(
            database,
            DetectionEventCreate(
                external_id=f"sandbox-{current_user.id}-{uuid4().hex[:12]}",
                source_type="portfolio-simulator",
                occurred_at=now,
                asset_id=f"sandbox-{current_user.id}",
                hostname=payload.hostname,
                ioc_type="ipv4",
                ioc_value=payload.source_ip or default_source,
                source_ip=payload.source_ip or default_source,
                destination_ip=payload.destination_ip,
                destination_port=port,
                predicted_label=payload.scenario,
                classifier_confidence=confidence,
                anomaly_score=anomaly,
                rule_score=rule_score,
                risk_score=risk,
                severity=severity,
                requires_review=risk >= 70,
            ),
            workspace="SANDBOX",
            owner_user_id=current_user.id,
            sandbox_expires_at=expires_at,
            commit=False,
        )
        incident_id = None
        if event.risk_score >= settings.auto_incident_risk_threshold:
            incident = create_incident(
                database,
                IncidentCreate(
                    title=f"[SANDBOX] {payload.scenario.replace('-', ' ').title()}",
                    severity=event.severity,
                    status="OPEN",
                    description=f"Automatically created from simulated event {event.id}",
                    detection_event_id=event.id,
                ),
                workspace="SANDBOX",
                owner_user_id=current_user.id,
                sandbox_expires_at=expires_at,
                commit=False,
            )
            incident_id = incident.id
        log_action(
            database,
            current_user.id,
            "SIMULATE_DETECTION_EVENT",
            f"Created sandbox event {event.id}",
            "DETECTION_EVENT",
            event.id,
            commit=False,
        )
    return SandboxSimulationRead(
        event=DetectionEventRead.model_validate(event),
        incident_id=incident_id,
        expires_at=expires_at,
    )


@router.post("/sandbox/reset")
def reset_sandbox(
    database: DatabaseSession,
    current_user=Depends(get_current_user),
) -> dict[str, int]:
    with atomic(database):
        events_deleted, incidents_deleted = reset_user_sandbox(database, current_user.id)
        log_action(
            database,
            current_user.id,
            "RESET_SANDBOX",
            f"Reset sandbox ({events_deleted} events, {incidents_deleted} incidents)",
            "USER",
            current_user.id,
            commit=False,
        )
    return {"events_deleted": events_deleted, "incidents_deleted": incidents_deleted}


@router.get("", response_model=list[DetectionEventRead])
def list_events(
    database: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    current_user=Depends(get_current_user),
) -> list[DetectionEventRead]:
    return list_detection_events(
        database,
        limit=limit,
        offset=offset,
        user_id=current_user.id,
        role=current_user.role,
    )


@router.get("/page", response_model=DetectionEventPage)
def page_events(
    database: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    severity: str | None = None,
    attack_type: str | None = None,
    source_ip: str | None = None,
    min_risk: Annotated[float | None, Query(ge=0, le=100)] = None,
    max_risk: Annotated[float | None, Query(ge=0, le=100)] = None,
    q: Annotated[str | None, Query(max_length=128)] = None,
    current_user=Depends(get_current_user),
) -> DetectionEventPage:
    items, total = search_detection_events(
        database,
        limit=limit,
        offset=offset,
        severity=severity,
        attack_type=attack_type,
        source_ip=source_ip,
        min_risk=min_risk,
        max_risk=max_risk,
        query=q,
        user_id=current_user.id,
        role=current_user.role,
    )

    return DetectionEventPage(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{event_id}", response_model=DetectionEventRead)
def get_event(
    event_id: int,
    database: DatabaseSession,
    current_user=Depends(get_current_user),
) -> DetectionEventRead:
    event = get_detection_event(
        database, event_id, user_id=current_user.id, role=current_user.role
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Detection event not found",
        )

    return event
