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


def test_create_and_list_incidents():
    payload = {
        "title": "Test Incident",
        "severity": "HIGH",
        "status": "OPEN",
        "description": "Testing incident creation",
        "detection_event_id": 1,
    }

    create_response = client.post(
        "/incidents",
        json=payload,
    )

    assert create_response.status_code == 201

    data = create_response.json()

    assert data["title"] == "Test Incident"
    assert data["severity"] == "HIGH"

    list_response = client.get("/incidents")

    assert list_response.status_code == 200

    incidents = list_response.json()

    assert len(incidents) >= 1


def test_get_incident_by_id():
    create_response = client.post(
        "/incidents",
        json={
            "title": "Detail Test Incident",
            "severity": "CRITICAL",
            "status": "OPEN",
            "description": "Testing incident detail",
            "detection_event_id": 1,
        },
    )

    assert create_response.status_code == 201

    incident_id = create_response.json()["id"]

    response = client.get(
        f"/incidents/{incident_id}",
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Detail Test Incident"


def test_incident_not_found():
    response = client.get("/incidents/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


def test_update_incident_status():
    create_response = client.post(
        "/incidents",
        json={
            "title": "Update Status Incident",
            "severity": "HIGH",
            "status": "OPEN",
            "description": "Testing status update",
            "detection_event_id": 1,
        },
    )

    assert create_response.status_code == 201

    incident_id = create_response.json()["id"]

    response = client.patch(
        f"/incidents/{incident_id}",
        json={
            "status": "RESOLVED",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "RESOLVED"
