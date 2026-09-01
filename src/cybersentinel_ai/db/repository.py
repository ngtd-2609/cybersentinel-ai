from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import DetectionEventCreate, IncidentCreate, IncidentUpdate
from cybersentinel_ai.db.models import DetectionEvent, Incident


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
) -> tuple[list[DetectionEvent], int]:
    filters = []

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
) -> Incident:
    incident = Incident(**payload.model_dump())

    database.add(incident)
    database.commit()
    database.refresh(incident)

    return incident


def list_incidents(
    database: Session,
    *,
    limit: int = 25,
    offset: int = 0,
) -> tuple[list[Incident], int]:
    count_statement = (
        select(func.count())
        .select_from(Incident)
    )

    total = int(database.scalar(count_statement) or 0)

    statement = (
        select(Incident)
        .order_by(Incident.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    items = list(database.scalars(statement).all())

    return items, total


def get_incident(
    database: Session,
    incident_id: int,
) -> Incident | None:
    return database.get(Incident, incident_id)


def update_incident_status(
    database: Session,
    incident_id: int,
    payload: IncidentUpdate,
) -> Incident | None:
    incident = database.get(Incident, incident_id)

    if incident is None:
        return None

    incident.status = payload.status

    database.commit()
    database.refresh(incident)

    return incident
