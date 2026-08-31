from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import IncidentCreate, IncidentRead
from cybersentinel_ai.db.database import get_db
from cybersentinel_ai.db.repository import (
    create_incident,
    list_incidents,
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
