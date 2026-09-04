from collections.abc import Generator
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from cybersentinel_ai.api.main import app
from cybersentinel_ai.db.database import Base, get_db
from cybersentinel_ai.db.models import AuditLog, DetectionEvent, Incident
from cybersentinel_ai.security.dependencies import get_current_user

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSession = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base.metadata.create_all(engine)


def override_get_db() -> Generator[Session, None, None]:
    database = TestingSession()

    try:
        yield database
    finally:
        database.close()


app.dependency_overrides[get_db] = override_get_db


def override_get_current_user():
    return SimpleNamespace(
        id=1,
        email="analyst@cybersentinel.ai",
        role="ANALYST",
        is_active=True,
    )


app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


def test_create_list_and_get_detection_event():
    payload = {
        "source_ip": "10.0.0.10",
        "destination_ip": "10.0.0.20",
        "destination_port": 443,
        "predicted_label": "DDoS",
        "classifier_confidence": 0.97,
        "anomaly_score": 0.82,
        "rule_score": 0.70,
        "risk_score": 88.4,
        "severity": "HIGH",
        "requires_review": False,
    }

    create_response = client.post("/events", json=payload)

    assert create_response.status_code == 201

    created = create_response.json()
    event_id = created["id"]

    get_response = client.get(f"/events/{event_id}")

    assert get_response.status_code == 200
    assert get_response.json()["predicted_label"] == "DDoS"

    list_response = client.get("/events")

    assert list_response.status_code == 200
    assert any(
        event["id"] == event_id
        for event in list_response.json()
    )


def test_detection_event_not_found():
    response = client.get("/events/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Detection event not found"


def test_viewer_cannot_create_detection_event():
    previous_override = app.dependency_overrides[get_current_user]
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=2,
        email="viewer@cybersentinel.ai",
        role="VIEWER",
        is_active=True,
    )

    try:
        response = client.post(
            "/events",
            json={
                "source_ip": "10.0.0.30",
                "destination_ip": "10.0.0.40",
                "destination_port": 443,
                "predicted_label": "DDoS",
                "classifier_confidence": 0.97,
                "anomaly_score": 0.82,
                "rule_score": 0.70,
                "risk_score": 88.4,
                "severity": "HIGH",
                "requires_review": False,
            },
        )
    finally:
        app.dependency_overrides[get_current_user] = previous_override

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_paginated_detection_events():
    response = client.get(
        "/events/page",
        params={
            "limit": 10,
            "offset": 0,
            "severity": "HIGH",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert all(
        event["severity"].upper() == "HIGH"
        for event in data["items"]
    )


def test_idempotency_key_prevents_duplicate_auto_incidents_and_audits():
    payload = {
        "source_ip": "198.51.100.25",
        "destination_ip": "203.0.113.80",
        "destination_port": 443,
        "predicted_label": "Web Attack",
        "classifier_confidence": 0.99,
        "anomaly_score": 0.95,
        "rule_score": 0.90,
        "risk_score": 99.0,
        "severity": "CRITICAL",
        "requires_review": True,
    }
    headers = {"Idempotency-Key": "sensor-a:packet-batch-20260904-1"}

    first = client.post("/events", json=payload, headers=headers)
    second = client.post("/events", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]

    event_id = first.json()["id"]
    database_dependency = app.dependency_overrides[get_db]()
    database = next(database_dependency)
    try:
        event_count = database.scalar(
            select(func.count())
            .select_from(DetectionEvent)
            .where(DetectionEvent.idempotency_key == headers["Idempotency-Key"])
        )
        incident_count = database.scalar(
            select(func.count())
            .select_from(Incident)
            .where(Incident.detection_event_id == event_id)
        )
        audit_count = database.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(
                AuditLog.action.in_(
                    ["CREATE_DETECTION_EVENT", "CREATE_INCIDENT_FROM_DETECTION"]
                ),
                AuditLog.description.contains(str(event_id)),
            )
        )
    finally:
        database_dependency.close()

    assert event_count == 1
    assert incident_count == 1
    assert audit_count == 2
