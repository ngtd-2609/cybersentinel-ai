from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from cybersentinel_ai.db.database import Base
from cybersentinel_ai.db.models import DetectionEvent


def test_detection_event_table_creation():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    inspector = inspect(engine)

    assert "detection_events" in inspector.get_table_names()

    columns = {
        column["name"]
        for column in inspector.get_columns("detection_events")
    }

    assert {
        "id",
        "source_ip",
        "destination_ip",
        "destination_port",
        "predicted_label",
        "classifier_confidence",
        "anomaly_score",
        "rule_score",
        "risk_score",
        "severity",
        "requires_review",
        "created_at",
    }.issubset(columns)

    assert DetectionEvent.__tablename__ == "detection_events"
