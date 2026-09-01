from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import IncidentCreate, IncidentPage, IncidentRead, IncidentUpdate
from cybersentinel_ai.db.database import get_db
from cybersentinel_ai.db.repository import (
    create_incident,
    get_incident,
    list_incidents,
    update_incident_status,
)

router = APIRouter(prefix="/incidents", tags=["Incidents"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=IncidentRead, status_code=201)
def create(
    payload: IncidentCreate,
    database: DatabaseSession,
) -> IncidentRead:
    return create_incident(database, payload)


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

    return incident
