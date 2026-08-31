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


def test_dashboard_summary():
    events = [
        {
            "source_ip": "10.0.0.10",
            "destination_ip": "10.0.0.20",
            "destination_port": 443,
            "predicted_label": "DDoS",
            "classifier_confidence": 0.97,
            "anomaly_score": 0.82,
            "rule_score": 0.70,
            "risk_score": 94.0,
            "severity": "CRITICAL",
            "requires_review": True,
        },
        {
            "source_ip": "10.0.0.10",
            "destination_ip": "10.0.0.30",
            "destination_port": 22,
            "predicted_label": "SSH-Patator",
            "classifier_confidence": 0.91,
            "anomaly_score": 0.65,
            "rule_score": 0.50,
            "risk_score": 78.0,
            "severity": "HIGH",
            "requires_review": False,
        },
    ]

    for event in events:
        response = client.post("/events", json=event)
        assert response.status_code == 201

    response = client.get("/dashboard/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["total_events"] >= 2
    assert data["critical_alerts"] >= 1
    assert data["high_alerts"] >= 1
    assert data["requires_review"] >= 1
    assert data["average_risk_score"] > 0
    assert len(data["top_attack_types"]) >= 1
    assert len(data["top_threat_sources"]) >= 1
    assert len(data["timeline"]) == 24
    assert sum(point["total"] for point in data["timeline"]) >= 2
    assert len(data["recent_events"]) >= 2
