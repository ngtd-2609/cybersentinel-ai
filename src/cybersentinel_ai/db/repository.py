from sqlalchemy import select
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import DetectionEventCreate
from cybersentinel_ai.db.models import DetectionEvent


def create_detection_event(
    database: Session,
    payload: DetectionEventCreate,
) -> DetectionEvent:
    event = DetectionEvent(**payload.model_dump())

    database.add(event)
    database.commit()
    database.refresh(event)

    return event


def get_detection_event(
    database: Session,
    event_id: int,
) -> DetectionEvent | None:
    return database.get(DetectionEvent, event_id)


def list_detection_events(
    database: Session,
    limit: int = 100,
    offset: int = 0,
) -> list[DetectionEvent]:
    statement = (
        select(DetectionEvent)
        .order_by(DetectionEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    return list(database.scalars(statement).all())
