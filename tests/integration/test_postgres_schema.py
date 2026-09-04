import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from cybersentinel_ai.db.models import (
    AuditLog,
    DetectionEvent,
    Incident,
    IncidentTimeline,
    User,
    UserSession,
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
        "user_sessions",
    }
    assert expected_tables <= set(inspect(engine).get_table_names())
    inspector = inspect(engine)
    assert inspector.get_foreign_keys("incidents")[0]["referred_table"] == "detection_events"
    assert inspector.get_foreign_keys("incident_timelines")[0]["referred_table"] == "incidents"
    assert inspector.get_foreign_keys("audit_logs")[0]["referred_table"] == "users"
    detection_indexes = {
        index["name"]: index for index in inspector.get_indexes("detection_events")
    }
    assert detection_indexes["ix_detection_events_idempotency_key"]["unique"]

    now = datetime.now(UTC)
    with Session(engine) as session:
        event = DetectionEvent(
            idempotency_key="ci-database-acceptance-event",
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

        user_session = UserSession(
            user_id=user.id,
            refresh_token_hash="a" * 64,
            expires_at=now + timedelta(days=7),
            created_at=now,
            ip_address="127.0.0.1",
            user_agent="CI integration test",
        )
        session.add(user_session)
        session.flush()
        user_session_id = user_session.id

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
        timeline = session.scalar(
            select(IncidentTimeline).where(IncidentTimeline.incident_id == stored.id)
        )
        audit_log = session.scalar(select(AuditLog).where(AuditLog.target_id == stored.id))
        assert timeline is not None
        assert audit_log is not None
        timeline_id = timeline.id

        session.delete(event)
        session.commit()
        session.refresh(stored)
        assert stored.detection_event_id is None

        session.delete(user)
        session.commit()
        session.refresh(audit_log)
        assert audit_log.user_id is None
        assert session.get(UserSession, user_session_id) is None

        session.delete(stored)
        session.commit()
        assert session.get(Incident, stored.id) is None
        assert session.get(IncidentTimeline, timeline_id) is None

    engine.dispose()
