import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from cybersentinel_ai.db.models import (
    AuditLog,
    DetectionEvent,
    Incident,
    IncidentTimeline,
    User,
)

pytestmark = pytest.mark.skipif(
    os.getenv("CYBERSENTINEL_RUN_POSTGRES_INTEGRATION") != "1",
    reason="requires the disposable PostgreSQL service used by CI",
)


def test_migrated_schema_supports_core_crud() -> None:
    database_url = os.environ["CYBERSENTINEL_DATABASE_URL"]
    engine = create_engine(database_url, pool_pre_ping=True)

    expected_tables = {
        "alembic_version",
        "audit_logs",
        "detection_events",
        "incident_timelines",
        "incidents",
        "users",
    }
    assert expected_tables <= set(inspect(engine).get_table_names())

    now = datetime.now(UTC)
    with Session(engine) as session:
        event = DetectionEvent(
            source_ip="198.51.100.10",
            destination_ip="203.0.113.20",
            destination_port=443,
            predicted_label="Web Attack",
            classifier_confidence=0.97,
            anomaly_score=0.88,
            rule_score=0.75,
            risk_score=92.0,
            severity="CRITICAL",
            requires_review=True,
            created_at=now,
        )
        session.add(event)
        session.flush()

        incident = Incident(
            title="CI database acceptance incident",
            severity="CRITICAL",
            status="OPEN",
            description="Created by the disposable PostgreSQL integration test.",
            detection_event_id=event.id,
            created_at=now,
        )
        user = User(
            email="ci-admin@example.test",
            username="ci-admin",
            hashed_password="not-a-real-password-hash",
            full_name="CI Admin",
            role="ADMIN",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        session.add_all([incident, user])
        session.flush()

        session.add_all(
            [
                IncidentTimeline(
                    incident_id=incident.id,
                    action="CREATED",
                    description="Incident created during acceptance testing.",
                    created_at=now,
                ),
                AuditLog(
                    user_id=user.id,
                    action="CREATE_INCIDENT",
                    target_type="incident",
                    target_id=incident.id,
                    description="CI database acceptance audit record.",
                    created_at=now,
                ),
            ]
        )
        session.commit()

        stored = session.scalar(
            select(Incident).where(Incident.title == "CI database acceptance incident")
        )
        assert stored is not None
        assert stored.detection_event is not None
        assert stored.detection_event.risk_score == 92.0
        assert session.scalar(
            select(IncidentTimeline).where(IncidentTimeline.incident_id == stored.id)
        )
        assert session.scalar(select(AuditLog).where(AuditLog.target_id == stored.id))

        session.delete(stored)
        session.commit()
        assert session.get(Incident, stored.id) is None

    engine.dispose()
