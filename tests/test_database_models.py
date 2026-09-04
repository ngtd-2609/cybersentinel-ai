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
        "idempotency_key",
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

    incident_foreign_keys = inspector.get_foreign_keys("incidents")
    timeline_foreign_keys = inspector.get_foreign_keys("incident_timelines")
    audit_foreign_keys = inspector.get_foreign_keys("audit_logs")

    assert incident_foreign_keys[0]["referred_table"] == "detection_events"
    assert timeline_foreign_keys[0]["referred_table"] == "incidents"
    assert audit_foreign_keys[0]["referred_table"] == "users"

    incident_indexes = {index["name"] for index in inspector.get_indexes("incidents")}
    assert "ix_incidents_detection_event_id" in incident_indexes
    assert "ix_incidents_created_at" in incident_indexes

    detection_indexes = {
        index["name"]: index for index in inspector.get_indexes("detection_events")
    }
    assert detection_indexes["ix_detection_events_idempotency_key"]["unique"] == 1
