import json
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from cybersentinel_ai.api.main import app
from cybersentinel_ai.api.schemas import IngestionEventCreate
from cybersentinel_ai.db.database import Base, get_db
from cybersentinel_ai.db.models import DetectionEvent, ModelVersion
from cybersentinel_ai.evaluation.phase_k import (
    DEFAULT_REPORT,
    build_reliability_report,
)
from cybersentinel_ai.ingestion.service import create_ingestion_job, process_ingestion_job
from cybersentinel_ai.mlops.service import population_stability_index
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
        id=501,
        email="mlops-admin@example.test",
        role="ADMIN",
        is_active=True,
    )


def model_payload(version: str, *, recall: float = 0.9) -> dict:
    return {
        "name": "xgboost-binary",
        "version": version,
        "task": "BINARY_CLASSIFICATION",
        "artifact_uri": f"artifacts/xgboost/{version}/model.joblib.dvc",
        "artifact_hash": f"artifact-{version}",
        "dataset_uri": "data/processed/cicids2017_binary.dvc",
        "dataset_hash": "136d82c2aa02afd4668d9bcc18d39a1a.dir",
        "git_commit": "11efc789e64a19f0b2a748e23eb4441e234d7abc",
        "metrics": {
            "precision": 0.98,
            "recall": recall,
            "f1": 0.93,
            "false_positive_rate": 0.01,
        },
    }


def monitoring_payload() -> dict:
    values = [float(index) for index in range(20)]
    return {
        "window_start": datetime.now(UTC).isoformat(),
        "window_end": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        "features": {"flow_duration": {"reference": values, "current": values}},
        "predictions": {"reference": values, "current": values},
    }


def test_registry_promotion_monitoring_comparison_provenance_and_feedback() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)
    try:
        with TestingSession() as database:
            champion = ModelVersion(
                **model_payload("1.0.0", recall=0.3),
                stage="PRODUCTION",
            )
            database.add(champion)
            database.commit()
            database.refresh(champion)
            champion_id = champion.id

        invalid = model_payload("1.0.1")
        del invalid["metrics"]["false_positive_rate"]
        assert client.post("/mlops/models", json=invalid).status_code == 422

        created = client.post("/mlops/models", json=model_payload("2.0.0"))
        assert created.status_code == 201
        challenger_id = created.json()["id"]
        assert created.json()["stage"] == "CANDIDATE"

        comparison = client.post(
            "/mlops/models/compare",
            json={"champion_id": champion_id, "challenger_id": challenger_id},
        )
        assert comparison.status_code == 200
        assert comparison.json()["recommended_model_id"] == challenger_id

        staged = client.post(
            f"/mlops/models/{challenger_id}/promote",
            json={"target_stage": "STAGING", "reason": "Passed offline evaluation"},
        )
        assert staged.status_code == 200
        assert staged.json()["stage"] == "STAGING"

        blocked = client.post(
            f"/mlops/models/{challenger_id}/promote",
            json={"target_stage": "PRODUCTION", "reason": "No drift report yet"},
        )
        assert blocked.status_code == 409

        monitoring = client.post(
            f"/mlops/models/{challenger_id}/monitoring",
            json=monitoring_payload(),
        )
        assert monitoring.status_code == 200
        assert monitoring.json()["status"] == "HEALTHY"

        promoted = client.post(
            f"/mlops/models/{challenger_id}/promote",
            json={"target_stage": "PRODUCTION", "reason": "Healthy staging window"},
        )
        assert promoted.status_code == 200
        assert promoted.json()["stage"] == "PRODUCTION"

        with TestingSession() as database:
            assert database.get(ModelVersion, champion_id).stage == "ARCHIVED"
            job, duplicate = create_ingestion_job(
                database,
                IngestionEventCreate(
                    external_id="phase-k-auto-provenance",
                    source_type="model-serving",
                    occurred_at=datetime.now(UTC),
                    predicted_label="PortScan",
                    classifier_confidence=0.95,
                    anomaly_score=0.8,
                    rule_score=0.7,
                    risk_score=90,
                    severity="HIGH",
                    requires_review=True,
                ),
                max_attempts=2,
            )
            assert duplicate is False
            database.commit()
            result = process_ingestion_job(database, job.id)
            database.commit()
            event = database.get(DetectionEvent, result["event_id"])
            assert event is not None
            assert event.model_version_id == challenger_id
            event_id = event.id

        provenance = client.get(f"/mlops/detections/{event_id}/provenance")
        assert provenance.status_code == 200
        assert provenance.json()["model"]["dataset_hash"].endswith(".dir")

        feedback = client.put(
            f"/mlops/detections/{event_id}/feedback",
            json={"verdict": "TRUE_POSITIVE", "notes": "Confirmed in firewall logs"},
        )
        assert feedback.status_code == 200
        assert feedback.json()["verdict"] == "TRUE_POSITIVE"
        summary = client.get(f"/mlops/models/{challenger_id}/feedback-summary")
        assert summary.json()["confirmed_precision"] == 1.0
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_drift_and_fixed_reliability_report_are_reproducible() -> None:
    values = [float(index) for index in range(20)]
    assert population_stability_index(values, values) == 0.0
    assert population_stability_index(values, [value + 100 for value in values]) > 0.3

    generated = build_reliability_report()
    committed = json.loads(DEFAULT_REPORT.read_text(encoding="utf-8"))
    assert generated == committed
    assert generated["release_gate_passed"] is True
