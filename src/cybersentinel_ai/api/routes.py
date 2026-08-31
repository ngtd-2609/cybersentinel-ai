from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import (
    DetectionEventCreate,
    DetectionEventPage,
    DetectionEventRead,
)
from cybersentinel_ai.db.database import get_db
from cybersentinel_ai.db.repository import (
    create_detection_event,
    get_detection_event,
    list_detection_events,
    search_detection_events,
)

router = APIRouter(prefix="/events", tags=["Detection Events"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=DetectionEventRead, status_code=201)
def create_event(
    payload: DetectionEventCreate,
    database: DatabaseSession,
) -> DetectionEventRead:
    return create_detection_event(database, payload)


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
