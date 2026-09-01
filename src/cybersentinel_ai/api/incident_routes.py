from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import IncidentCreate, IncidentRead, IncidentUpdate
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


@router.get("", response_model=list[IncidentRead])
def list_all(
    database: DatabaseSession,
) -> list[IncidentRead]:
    return list_incidents(database)


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
