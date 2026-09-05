from datetime import UTC, datetime

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from cybersentinel_ai.api.schemas import AlertRuleRead, AlertRuleUpdate, IngestionEventCreate
from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.database import Base
from cybersentinel_ai.db.models import (
    AlertRule,
    DetectionEvent,
    Incident,
    IncidentDetection,
    NotificationDelivery,
)
from cybersentinel_ai.ingestion.notifications import deliver_notification
from cybersentinel_ai.ingestion.service import (
    create_ingestion_job,
    mark_job_failed,
    process_ingestion_job,
)


@pytest.fixture
def database() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def event(external_id: str, *, risk_score: float = 91.0) -> IngestionEventCreate:
    return IngestionEventCreate(
        external_id=external_id,
        source_type="edr-agent",
        occurred_at=datetime.now(UTC),
        asset_id="asset-42",
        hostname="workstation-42",
        affected_user="analyst@example.test",
        ioc_type="sha256",
        ioc_value="a" * 64,
        correlation_key="asset-42:ransomware",
        source_ip="198.51.100.42",
        destination_ip="203.0.113.10",
        destination_port=443,
        predicted_label="Ransomware",
        classifier_confidence=0.98,
        anomaly_score=0.94,
        rule_score=0.9,
        risk_score=risk_score,
        severity="CRITICAL",
        requires_review=True,
    )


def test_pipeline_deduplicates_correlates_and_queues_notification(
    database: Session,
) -> None:
    database.add(
        AlertRule(
            name="critical-edr",
            enabled=True,
            priority=1,
            min_risk_score=80,
            severities="CRITICAL,HIGH",
            label_pattern="ransom",
            require_review=True,
            auto_create_incident=True,
            notification_channels="webhook",
        )
    )
    database.commit()

    first_job, duplicate = create_ingestion_job(database, event("evt-1"), max_attempts=3)
    database.commit()
    assert duplicate is False
    first_result = process_ingestion_job(database, first_job.id)
    database.commit()

    second_job, duplicate = create_ingestion_job(database, event("evt-2"), max_attempts=3)
    database.commit()
    assert duplicate is False
    second_result = process_ingestion_job(database, second_job.id)
    database.commit()

    existing_job, duplicate = create_ingestion_job(database, event("evt-1"), max_attempts=3)
    assert duplicate is True
    assert existing_job.id == first_job.id
    assert first_result["incident_id"] == second_result["incident_id"]

    incident = database.get(Incident, first_result["incident_id"])
    assert incident is not None
    assert incident.event_count == 2
    assert incident.severity == "CRITICAL"
    assert database.scalar(select(func.count()).select_from(DetectionEvent)) == 2
    assert database.scalar(select(func.count()).select_from(IncidentDetection)) == 2
    assert database.scalar(select(func.count()).select_from(NotificationDelivery)) == 2

    stored_event = database.get(DetectionEvent, first_result["event_id"])
    assert stored_event is not None
    assert stored_event.hostname == "workstation-42"
    assert stored_event.affected_user == "analyst@example.test"
    assert stored_event.ioc_value == "a" * 64


def test_job_and_notification_reach_dead_letter(database: Session, monkeypatch) -> None:
    job, _ = create_ingestion_job(database, event("evt-failure"), max_attempts=2)
    database.commit()
    assert mark_job_failed(database, job.id, RuntimeError("first failure")) == "RETRY"
    assert mark_job_failed(database, job.id, RuntimeError("last failure")) == "DEAD_LETTER"

    stored_event = DetectionEvent(
        predicted_label="Malware",
        classifier_confidence=0.9,
        anomaly_score=0.8,
        rule_score=0.7,
        risk_score=90,
        severity="CRITICAL",
        requires_review=True,
    )
    database.add(stored_event)
    database.flush()
    delivery = NotificationDelivery(
        detection_event_id=stored_event.id,
        channel="webhook",
        max_attempts=2,
    )
    database.add(delivery)
    database.commit()
    monkeypatch.setattr(get_settings(), "notification_webhook_url", "https://hook.test")
    transport = httpx.MockTransport(lambda request: httpx.Response(503, request=request))
    assert deliver_notification(database, delivery.id, transport=transport) == "RETRY"
    assert deliver_notification(database, delivery.id, transport=transport) == "DEAD_LETTER"


def test_notification_success_and_rule_schema(database: Session, monkeypatch) -> None:
    stored_event = DetectionEvent(
        predicted_label="Credential Theft",
        classifier_confidence=0.95,
        anomaly_score=0.85,
        rule_score=0.8,
        risk_score=95,
        severity="CRITICAL",
        requires_review=True,
    )
    database.add(stored_event)
    database.flush()
    delivery = NotificationDelivery(
        detection_event_id=stored_event.id,
        channel="webhook",
        max_attempts=2,
    )
    database.add(delivery)
    database.commit()
    monkeypatch.setattr(get_settings(), "notification_webhook_url", "https://hook.test")
    transport = httpx.MockTransport(lambda request: httpx.Response(204, request=request))
    assert deliver_notification(database, delivery.id, transport=transport) == "SENT"

    rule = AlertRule(
        id=1,
        name="schema-rule",
        enabled=True,
        priority=100,
        min_risk_score=0,
        severities="CRITICAL,HIGH",
        label_pattern=None,
        require_review=False,
        auto_create_incident=False,
        notification_channels="webhook,slack",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    serialized = AlertRuleRead.model_validate(rule)
    assert serialized.severities == ["CRITICAL", "HIGH"]
    assert serialized.notification_channels == ["webhook", "slack"]
    assert AlertRuleUpdate(severities=["high"]).severities == ["HIGH"]


def test_ingestion_timestamp_requires_timezone() -> None:
    payload = event("evt-naive").model_dump()
    payload["occurred_at"] = datetime(2026, 9, 5, 12, 0, tzinfo=UTC).replace(tzinfo=None)
    with pytest.raises(ValidationError, match="must include a timezone"):
        IngestionEventCreate.model_validate(payload)


def test_ingestion_normalizes_identity_and_rejects_invalid_severity() -> None:
    normalized = event("evt-normalized").model_copy(
        update={"external_id": " evt-normalized ", "source_type": " edr-agent "}
    )
    reparsed = IngestionEventCreate.model_validate(normalized.model_dump())
    assert reparsed.external_id == "evt-normalized"
    assert reparsed.source_type == "edr-agent"

    payload = event("evt-invalid-severity").model_dump()
    payload["severity"] = "urgent"
    with pytest.raises(ValidationError, match="invalid severity"):
        IngestionEventCreate.model_validate(payload)
