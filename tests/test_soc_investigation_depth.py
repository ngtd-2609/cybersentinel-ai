from collections.abc import Generator
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from cybersentinel_ai.api import incident_routes, investigation_routes
from cybersentinel_ai.api.schemas import DetectionEventCreate, IncidentCreate
from cybersentinel_ai.core.config import Settings
from cybersentinel_ai.db.database import Base, get_db
from cybersentinel_ai.db.models import (
    IncidentDetection,
    ResponseAction,
    ThreatIntelCache,
)
from cybersentinel_ai.db.repository import (
    create_detection_event,
    create_incident,
    list_incidents,
)
from cybersentinel_ai.security.dependencies import get_current_user
from cybersentinel_ai.threat_intel.providers import ThreatIntelResult


def build_client(role: str = "ADMIN") -> tuple[TestClient, sessionmaker]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_database() -> Generator[Session, None, None]:
        with factory() as database:
            yield database

    app = FastAPI()
    app.include_router(incident_routes.router)
    app.include_router(investigation_routes.router)
    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1,
        email="analyst@example.test",
        role=role,
        is_active=True,
    )
    return TestClient(app), factory


def test_asset_relation_case_filters_and_correlated_detections() -> None:
    client, factory = build_client()
    created_asset = client.post(
        "/assets",
        json={
            "id": "prod-web-01",
            "hostname": "PROD-WEB-01",
            "primary_ip": "10.20.0.15",
            "operating_system": "Ubuntu 24.04",
            "environment": "PROD",
            "criticality": "CRITICAL",
            "owner_team": "Platform",
            "internet_facing": True,
            "status": "ONLINE",
        },
    )
    assert created_asset.status_code == 201

    with factory() as database:
        first = create_detection_event(
            database,
            DetectionEventCreate(
                asset_id="prod-web-01",
                hostname="PROD-WEB-01",
                source_ip="203.0.113.10",
                predicted_label="RANSOMWARE",
                classifier_confidence=0.98,
                anomaly_score=0.96,
                rule_score=1,
                risk_score=98,
                severity="CRITICAL",
                requires_review=True,
            ),
        )
        second = create_detection_event(
            database,
            DetectionEventCreate(
                asset_id="prod-web-01",
                hostname="PROD-WEB-01",
                source_ip="203.0.113.10",
                predicted_label="C2-TRAFFIC",
                classifier_confidence=0.94,
                anomaly_score=0.92,
                rule_score=0.9,
                risk_score=94,
                severity="CRITICAL",
                requires_review=True,
            ),
        )
        incident = create_incident(
            database,
            IncidentCreate(
                title="Ransomware chain",
                severity="CRITICAL",
                detection_event_id=first.id,
                priority="P1",
            ),
        )
        database.add(
            IncidentDetection(incident_id=incident.id, detection_event_id=second.id)
        )
        incident.event_count = 2
        database.commit()
        items, total = list_incidents(
            database,
            asset_id="prod-web-01",
            attack_type="C2",
            source_ip="203.0.113",
            priority="P1",
        )
        assert total == 1
        assert items[0].id == incident.id
        incident_id = incident.id

    detail = client.get(f"/incidents/{incident_id}")
    assert detail.status_code == 200
    assert detail.json()["display_id"].startswith("CS-")
    assert detail.json()["affected_assets"][0]["hostname"] == "PROD-WEB-01"
    assert len(detail.json()["related_detections"]) == 2


def test_viewer_can_simulate_response_only_in_own_sandbox() -> None:
    client, factory = build_client(role="VIEWER")
    with factory() as database:
        incident = create_incident(
            database,
            IncidentCreate(title="Private sandbox", severity="HIGH"),
            workspace="SANDBOX",
            owner_user_id=1,
        )
        incident_id = incident.id

    response = client.post(
        f"/incidents/{incident_id}/responses/simulate",
        json={"action": "BLOCK_SOURCE_IP", "target": "203.0.113.8"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "SIMULATED_SUCCESS"
    assert response.json()["simulation"] is True
    with factory() as database:
        assert database.scalar(select(func.count()).select_from(ResponseAction)) == 1


def test_abuseipdb_provider_result_is_cached(monkeypatch) -> None:
    client, factory = build_client()
    calls = 0

    def fake_enrich(_provider, indicator: str) -> ThreatIntelResult:
        nonlocal calls
        calls += 1
        return ThreatIntelResult(
            provider="AbuseIPDB",
            indicator=indicator,
            reputation="MALICIOUS",
            abuse_confidence=92,
            country="US",
            reports=47,
            last_reported_at="2026-09-06T12:00:00Z",
        )

    monkeypatch.setattr(
        investigation_routes,
        "get_settings",
        lambda: Settings(_env_file=None, abuseipdb_api_key="test-provider-key"),
    )
    monkeypatch.setattr(
        investigation_routes.AbuseIPDBProvider,
        "enrich_ip",
        fake_enrich,
    )

    first = client.get("/threat-intel/ip/203.0.113.42")
    second = client.get("/threat-intel/ip/203.0.113.42")
    assert first.status_code == second.status_code == 200
    assert first.json()["abuse_confidence"] == 92
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert calls == 1
    with factory() as database:
        assert database.scalar(select(func.count()).select_from(ThreatIntelCache)) == 1
