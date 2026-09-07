from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import (
    IncidentCreate,
    IncidentPage,
    IncidentRead,
    IncidentSummary,
    IncidentTimelineCreate,
    IncidentTimelineRead,
    IncidentUpdate,
)
from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.db.database import atomic, get_db
from cybersentinel_ai.db.repository import (
    create_incident,
    create_incident_timeline,
    get_incident,
    list_incident_timelines,
    list_incidents,
    summarize_incidents,
    update_incident_status,
)
from cybersentinel_ai.security.dependencies import get_current_user
from cybersentinel_ai.security.rbac import UserRole, require_role

router = APIRouter(prefix="/incidents", tags=["Incidents"])

DatabaseSession = Annotated[Session, Depends(get_db)]


def can_modify_incident(current_user, incident) -> bool:
    return current_user.role in {
        UserRole.ADMIN.value,
        UserRole.SENIOR_ANALYST.value,
        UserRole.ANALYST.value,
    } or (
        incident.workspace == "SANDBOX" and incident.owner_user_id == current_user.id
    )


@router.post("", response_model=IncidentRead, status_code=201)
def create(
    payload: IncidentCreate,
    database: DatabaseSession,
    current_user=Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.SENIOR_ANALYST,
            UserRole.ANALYST,
        )
    ),
) -> IncidentRead:
    linked_event = None
    if payload.detection_event_id is not None:
        from cybersentinel_ai.db.repository import get_detection_event

        linked_event = get_detection_event(
            database,
            payload.detection_event_id,
            user_id=current_user.id,
            role=current_user.role,
        )
        if linked_event is None:
            raise HTTPException(status_code=404, detail="Detection event not found")
    with atomic(database):
        incident = create_incident(
            database,
            payload,
            workspace="SANDBOX",
            owner_user_id=current_user.id,
            sandbox_expires_at=(
                linked_event.sandbox_expires_at if linked_event is not None else None
            ),
            commit=False,
        )

        log_action(
            database,
            current_user.id,
            "CREATE_INCIDENT",
            f"Created incident {incident.id}",
            "INCIDENT",
            incident.id,
            commit=False,
        )

    return incident


@router.get("", response_model=IncidentPage)
def list_all(
    database: DatabaseSession,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: str | None = Query(default=None, alias="status", max_length=32),
    severity: str | None = Query(default=None, max_length=16),
    priority: str | None = Query(default=None, max_length=8),
    assignee_user_id: int | None = Query(default=None, ge=1),
    asset_id: str | None = Query(default=None, max_length=128),
    attack_type: str | None = Query(default=None, max_length=128),
    source_ip: str | None = Query(default=None, max_length=45),
    query: str | None = Query(default=None, max_length=255),
    since: datetime | None = None,
    until: datetime | None = None,
    current_user=Depends(get_current_user),
) -> IncidentPage:
    items, total = list_incidents(
        database,
        limit=limit,
        offset=offset,
        user_id=current_user.id,
        role=current_user.role,
        status=status_filter,
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

    return IncidentPage(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/summary", response_model=IncidentSummary)
def summary(
    database: DatabaseSession,
    severity: str | None = Query(default=None, max_length=16),
    priority: str | None = Query(default=None, max_length=8),
    assignee_user_id: int | None = Query(default=None, ge=1),
    asset_id: str | None = Query(default=None, max_length=128),
    attack_type: str | None = Query(default=None, max_length=128),
    source_ip: str | None = Query(default=None, max_length=45),
    query: str | None = Query(default=None, max_length=255),
    since: datetime | None = None,
    until: datetime | None = None,
    current_user=Depends(get_current_user),
) -> IncidentSummary:
    aggregates = summarize_incidents(
        database,
        user_id=current_user.id,
        role=current_user.role,
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
    return IncidentSummary(**aggregates)


@router.get("/{incident_id}", response_model=IncidentRead)
def get_by_id(
    incident_id: int,
    database: DatabaseSession,
    current_user=Depends(get_current_user),
) -> IncidentRead:
    incident = get_incident(
        database, incident_id, user_id=current_user.id, role=current_user.role
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return incident


@router.patch("/{incident_id}", response_model=IncidentRead)
def update_status(
    incident_id: int,
    payload: IncidentUpdate,
    database: DatabaseSession,
    current_user=Depends(get_current_user),
) -> IncidentRead:
    incident = get_incident(
        database, incident_id, user_id=current_user.id, role=current_user.role
    )
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if not can_modify_incident(current_user, incident):
        raise HTTPException(status_code=403, detail="Incident update is not permitted")
    if incident.workspace == "DEMO" and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Demo incidents are read-only")
    with atomic(database):
        incident = update_incident_status(
            database,
            incident_id,
            payload,
            commit=False,
        )

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found",
            )

        log_action(
            database,
            current_user.id,
            "UPDATE_INCIDENT_STATUS",
            f"Updated incident {incident.id}",
            "INCIDENT",
            incident.id,
            commit=False,
        )

    return incident


@router.post("/{incident_id}/timeline", response_model=IncidentTimelineRead)
def create_timeline(
    incident_id: int,
    payload: IncidentTimelineCreate,
    database: DatabaseSession,
    current_user=Depends(get_current_user),
) -> IncidentTimelineRead:
    incident = get_incident(
        database, incident_id, user_id=current_user.id, role=current_user.role
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )
    if not can_modify_incident(current_user, incident):
        raise HTTPException(status_code=403, detail="Incident update is not permitted")
    if incident.workspace == "DEMO" and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Demo incidents are read-only")

    with atomic(database):
        timeline = create_incident_timeline(
            database,
            incident_id,
            payload,
            commit=False,
        )

        log_action(
            database,
            current_user.id,
            "CREATE_INCIDENT_TIMELINE",
            f"Added timeline to incident {incident_id}",
            "INCIDENT",
            incident_id,
            commit=False,
        )

    return timeline


@router.get("/{incident_id}/timeline", response_model=list[IncidentTimelineRead])
def get_timelines(
    incident_id: int,
    database: DatabaseSession,
    current_user=Depends(get_current_user),
) -> list[IncidentTimelineRead]:
    incident = get_incident(
        database, incident_id, user_id=current_user.id, role=current_user.role
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return list_incident_timelines(
        database,
        incident_id,
    )
