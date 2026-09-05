from collections.abc import Generator
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from cybersentinel_ai.api import ingestion_routes
from cybersentinel_ai.api.main import app
from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.database import Base, get_db
from cybersentinel_ai.db.models import AlertRule
from cybersentinel_ai.ingestion.service import process_ingestion_job
from cybersentinel_ai.security.dependencies import get_current_user

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(engine)


def override_get_db() -> Generator[Session, None, None]:
    with TestingSession() as database:
        yield database


def override_get_current_user():
    return SimpleNamespace(
        id=1,
        email="phase-j-admin@example.test",
        role="ADMIN",
        is_active=True,
    )


def payload() -> dict:
    return {
        "events": [
            {
                "external_id": "api-ingestion-event-1",
                "source_type": "edr-agent",
                "occurred_at": "2026-09-05T12:00:00Z",
                "hostname": "api-workstation",
                "correlation_key": "api-workstation:malware",
                "predicted_label": "Malware",
                "classifier_confidence": 0.95,
                "anomaly_score": 0.9,
                "rule_score": 0.85,
                "risk_score": 95,
                "severity": "critical",
                "requires_review": True,
            }
        ]
    }


def test_ingestion_api_dedup_trace_and_rule_management(monkeypatch) -> None:
    async def no_publish(_payload: dict) -> None:
        return None

    monkeypatch.setattr(get_settings(), "ingestion_api_keys", "api-test-key")
    monkeypatch.setattr(ingestion_routes, "publish_update", no_publish)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)
    try:
        with TestingSession() as database:
            database.add(
                AlertRule(
                    name="api-ingestion-critical",
                    enabled=True,
                    priority=1,
                    min_risk_score=90,
                    severities="CRITICAL",
                    require_review=True,
                    auto_create_incident=True,
                    notification_channels="webhook",
                )
            )
            database.commit()

        unauthorized = client.post("/ingest/events", json=payload())
        assert unauthorized.status_code == 401

        accepted = client.post(
            "/ingest/events",
            json=payload(),
            headers={"X-Ingestion-Key": "api-test-key"},
        )
        assert accepted.status_code == 202
        assert accepted.json()["accepted"] == 1
        assert accepted.json()["duplicates"] == 0
        job_id = accepted.json()["items"][0]["job_id"]

        duplicate = client.post(
            "/ingest/events",
            json=payload(),
            headers={"X-Ingestion-Key": "api-test-key"},
        )
        assert duplicate.status_code == 202
        assert duplicate.json()["duplicates"] == 1
        assert duplicate.json()["items"][0]["job_id"] == job_id

        with TestingSession() as database:
            result = process_ingestion_job(database, job_id)
            database.commit()
        assert result["status"] == "COMPLETED"

        trace = client.get(f"/ingest/jobs/{job_id}/trace")
        assert trace.status_code == 200
        assert trace.json()["job"]["status"] == "COMPLETED"
        assert trace.json()["detection_event"]["severity"] == "CRITICAL"
        assert trace.json()["incident_ids"]
        assert trace.json()["notifications"][0]["channel"] == "webhook"

        created_rule = client.post(
            "/alert-rules",
            json={
                "name": "api-managed-rule",
                "min_risk_score": 75,
                "severities": ["high"],
                "notification_channels": ["slack"],
            },
        )
        assert created_rule.status_code == 201
        assert created_rule.json()["severities"] == ["HIGH"]
        rule_id = created_rule.json()["id"]

        updated_rule = client.patch(
            f"/alert-rules/{rule_id}",
            json={"enabled": False, "notification_channels": ["webhook"]},
        )
        assert updated_rule.status_code == 200
        assert updated_rule.json()["enabled"] is False
        assert updated_rule.json()["notification_channels"] == ["webhook"]
        assert client.get("/alert-rules").status_code == 200
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
