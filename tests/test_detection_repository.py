from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from cybersentinel_ai.api.schemas import DetectionEventCreate
from cybersentinel_ai.db.database import Base
from cybersentinel_ai.db.repository import (
    create_detection_event,
    get_detection_event,
    list_detection_events,
)


def build_test_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    return Session(engine)


def test_detection_event_repository():
    database = build_test_session()

    payload = DetectionEventCreate(
        source_ip="10.0.0.10",
        destination_ip="10.0.0.20",
        destination_port=443,
        predicted_label="DDoS",
        classifier_confidence=0.96,
        anomaly_score=0.82,
        rule_score=0.70,
        risk_score=88.4,
        severity="HIGH",
        requires_review=False,
    )

    created = create_detection_event(database, payload)

    assert created.id is not None
    assert created.predicted_label == "DDoS"

    fetched = get_detection_event(database, created.id)

    assert fetched is not None
    assert fetched.id == created.id

    events = list_detection_events(database)

    assert len(events) == 1
    assert events[0].id == created.id

    database.close()
