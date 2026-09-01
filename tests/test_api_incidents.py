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
