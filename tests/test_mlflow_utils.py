from pathlib import Path

import mlflow

from cybersentinel_ai.training.mlflow_utils import (
    configure_mlflow,
    log_artifact_if_exists,
    log_metrics,
)


def test_mlflow_local_tracking(tmp_path: Path):
    database = tmp_path / "mlflow.db"
    tracking_uri = f"sqlite:///{database}"

    experiment_id = configure_mlflow(
        experiment_name="cybersentinel-test",
        tracking_uri=tracking_uri,
    )

    assert experiment_id

    artifact = tmp_path / "metrics.json"
    artifact.write_text('{"status": "ok"}')

    with mlflow.start_run():
        log_metrics(
            {
                "accuracy": 0.9,
                "f1": 0.8,
            }
        )
        log_artifact_if_exists(artifact)

    runs = mlflow.search_runs(
        experiment_ids=[experiment_id],
    )

    assert len(runs) == 1
    assert runs.iloc[0]["metrics.accuracy"] == 0.9
    assert runs.iloc[0]["metrics.f1"] == 0.8
