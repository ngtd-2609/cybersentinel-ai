import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from cybersentinel_ai.db.models import (
    AlertRule,
    AuditLog,
    DetectionEvent,
    DetectionFeedback,
    Incident,
    IncidentDetection,
    IncidentTimeline,
    IngestionJob,
    MfaChallenge,
    MfaRecoveryCode,
    ModelMonitoringReport,
    ModelStageTransition,
    ModelVersion,
    NotificationDelivery,
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
        "incident_detections",
        "alert_rules",
        "ingestion_jobs",
        "notification_deliveries",
        "model_versions",
        "model_stage_transitions",
        "model_monitoring_reports",
        "detection_feedback",
        "users",
        "user_sessions",
        "mfa_challenges",
        "mfa_recovery_codes",
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
    detection_columns = {
        column["name"] for column in inspector.get_columns("detection_events")
    }
    assert {
        "external_id",
        "source_type",
        "occurred_at",
        "asset_id",
        "hostname",
        "affected_user",
        "ioc_type",
        "ioc_value",
        "correlation_key",
        "model_version_id",
    } <= detection_columns
    incident_columns = {column["name"] for column in inspector.get_columns("incidents")}
    assert {"correlation_key", "event_count", "last_event_at"} <= incident_columns
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    assert {
        "failed_login_attempts",
        "locked_until",
        "last_failed_login_at",
        "mfa_enabled",
        "mfa_secret_encrypted",
        "mfa_pending_secret_encrypted",
    } <= user_columns
    user_indexes = {index["name"] for index in inspector.get_indexes("users")}
    assert "ix_users_locked_until" in user_indexes
    audit_columns = {column["name"] for column in inspector.get_columns("audit_logs")}
    assert {"request_id", "ip_address", "user_agent"} <= audit_columns
    audit_indexes = {index["name"] for index in inspector.get_indexes("audit_logs")}
    assert {"ix_audit_logs_request_id", "ix_audit_logs_ip_address"} <= audit_indexes

    now = datetime.now(UTC)
    with Session(engine) as session:
        registered_model = session.scalar(
            select(ModelVersion).where(ModelVersion.stage == "PRODUCTION")
        )
        assert registered_model is not None
        assert registered_model.artifact_hash == "35755c3ff01fa2973db3a8673f4f9e03"
        event = DetectionEvent(
            idempotency_key="ci-database-acceptance-event",
            external_id="ci-edr-event-1",
            source_type="ci-edr-agent",
            occurred_at=now,
            asset_id="ci-asset-1",
            hostname="ci-workstation",
            affected_user="ci-user@example.test",
            ioc_type="ipv4",
            ioc_value="198.51.100.10",
            correlation_key="ci-asset-1:web-attack",
            model_version_id=registered_model.id,
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
            correlation_key="ci-asset-1:web-attack",
            event_count=1,
            last_event_at=now,
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
                IncidentDetection(
                    incident_id=incident.id,
                    detection_event_id=event.id,
                ),
                AlertRule(
                    name="CI critical event rule",
                    enabled=True,
                    priority=1,
                    min_risk_score=90,
                    severities="CRITICAL",
                    auto_create_incident=True,
                    notification_channels="webhook",
                ),
                IngestionJob(
                    idempotency_key="ci-ingestion-job",
                    source_type="ci-edr-agent",
                    external_id="ci-edr-event-1",
                    payload={"external_id": "ci-edr-event-1"},
                    status="COMPLETED",
                    detection_event_id=event.id,
                ),
                NotificationDelivery(
                    detection_event_id=event.id,
                    incident_id=incident.id,
                    channel="webhook",
                ),
                ModelStageTransition(
                    model_version_id=registered_model.id,
                    from_stage="STAGING",
                    to_stage="PRODUCTION",
                    reason="CI acceptance transition",
                    actor_id=user.id,
                ),
                ModelMonitoringReport(
                    model_version_id=registered_model.id,
                    window_start=now - timedelta(hours=1),
                    window_end=now,
                    feature_drift_score=0.01,
                    prediction_drift_score=0.02,
                    status="HEALTHY",
                    details={"feature_psi": {"flow_duration": 0.01}},
                ),
                DetectionFeedback(
                    detection_event_id=event.id,
                    analyst_id=user.id,
                    verdict="TRUE_POSITIVE",
                    notes="CI confirmed",
                ),
            ]
        )

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

        recovery_code = MfaRecoveryCode(user_id=user.id, code_hash="b" * 64)
        challenge = MfaChallenge(
            user_id=user.id,
            expires_at=now + timedelta(minutes=5),
            ip_address="127.0.0.1",
            user_agent="CI integration test",
        )
        session.add_all([recovery_code, challenge])
        session.flush()
        recovery_code_id = recovery_code.id
        challenge_id = challenge.id

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
                    request_id="ci-request-id",
                    ip_address="127.0.0.1",
                    user_agent="CI integration test",
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
        assert stored.correlation_key == "ci-asset-1:web-attack"
        assert stored.detection_event.model_version_id == registered_model.id
        assert session.scalar(select(IncidentDetection.incident_id)) == stored.id
        assert session.scalar(select(IngestionJob.status)) == "COMPLETED"
        assert session.scalar(select(NotificationDelivery.channel)) == "webhook"
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
        assert session.get(MfaRecoveryCode, recovery_code_id) is None
        assert session.get(MfaChallenge, challenge_id) is None

        session.delete(stored)
        session.commit()
        assert session.get(Incident, stored.id) is None
        assert session.get(IncidentTimeline, timeline_id) is None

    engine.dispose()
