from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import (
    IncidentCreate,
    IncidentPage,
    IncidentRead,
    IncidentTimelineCreate,
    IncidentTimelineRead,
    IncidentUpdate,
)
from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.db.database import get_db
from cybersentinel_ai.db.repository import (
    create_incident,
    create_incident_timeline,
    get_incident,
    list_incident_timelines,
    list_incidents,
    update_incident_status,
)
from cybersentinel_ai.security.rbac import UserRole, require_role

router = APIRouter(prefix="/incidents", tags=["Incidents"])

DatabaseSession = Annotated[Session, Depends(get_db)]


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
    incident = create_incident(database, payload)

    log_action(
        database,
        current_user.id,
        "CREATE_INCIDENT",
        f"Created incident {incident.id}",
        "INCIDENT",
        incident.id,
    )

    return incident


@router.get("", response_model=IncidentPage)
def list_all(
    database: DatabaseSession,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> IncidentPage:
    items, total = list_incidents(
        database,
        limit=limit,
        offset=offset,
    )

    return IncidentPage(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{incident_id}", response_model=IncidentRead)
def get_by_id(
    incident_id: int,
    database: DatabaseSession,
) -> IncidentRead:
    incident = get_incident(database, incident_id)

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
    current_user=Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.SENIOR_ANALYST,
            UserRole.ANALYST,
        )
    ),
) -> IncidentRead:
    incident = update_incident_status(
        database,
        incident_id,
        payload,
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
    )

    return incident


@router.post("/{incident_id}/timeline", response_model=IncidentTimelineRead)
def create_timeline(
    incident_id: int,
    payload: IncidentTimelineCreate,
    database: DatabaseSession,
    current_user=Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.SENIOR_ANALYST,
            UserRole.ANALYST,
        )
    ),
) -> IncidentTimelineRead:
    incident = get_incident(database, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    timeline = create_incident_timeline(
        database,
        incident_id,
        payload,
    )

    log_action(
        database,
        current_user.id,
        "CREATE_INCIDENT_TIMELINE",
        f"Added timeline to incident {incident_id}",
        "INCIDENT",
        incident_id,
    )

    return timeline


@router.get("/{incident_id}/timeline", response_model=list[IncidentTimelineRead])
def get_timelines(
    incident_id: int,
    database: DatabaseSession,
) -> list[IncidentTimelineRead]:
    incident = get_incident(database, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return list_incident_timelines(
        database,
        incident_id,
    )
