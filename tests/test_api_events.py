from collections.abc import Generator
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from cybersentinel_ai.api.main import app
from cybersentinel_ai.db.database import Base, get_db
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
