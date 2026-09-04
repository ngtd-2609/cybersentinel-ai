from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import (
    DetectionEventCreate,
    DetectionEventPage,
    DetectionEventRead,
    IncidentCreate,
)
from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.database import atomic, get_db
from cybersentinel_ai.db.repository import (
    create_detection_event,
    create_incident,
    get_detection_event,
    get_detection_event_by_idempotency_key,
    list_detection_events,
    search_detection_events,
)
from cybersentinel_ai.security.rbac import UserRole, require_role

router = APIRouter(prefix="/events", tags=["Detection Events"])

DatabaseSession = Annotated[Session, Depends(get_db)]


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
) -> DetectionEventRead:
    if idempotency_key:
        existing = get_detection_event_by_idempotency_key(
            database,
            idempotency_key,
        )
        if existing is not None:
            return existing

    try:
        with atomic(database):
            event = create_detection_event(
                database,
                payload,
                idempotency_key=idempotency_key,
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


@router.get("", response_model=list[DetectionEventRead])
def list_events(
    database: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DetectionEventRead]:
    return list_detection_events(
        database,
        limit=limit,
        offset=offset,
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
) -> DetectionEventRead:
    event = get_detection_event(database, event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Detection event not found",
        )

    return event
