from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from cybersentinel_ai.api.main import app
from cybersentinel_ai.db.database import Base, get_db

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
