from pathlib import Path

import mlflow


def configure_mlflow(
    experiment_name: str,
    tracking_uri: str = "sqlite:///mlflow.db",
) -> str:
    mlflow.set_tracking_uri(tracking_uri)

    experiment = mlflow.get_experiment_by_name(experiment_name)

    if experiment is None:
        experiment_id = mlflow.create_experiment(experiment_name)
    else:
        experiment_id = experiment.experiment_id

    mlflow.set_experiment(experiment_name)

    return str(experiment_id)


def log_metrics(metrics: dict[str, float]) -> None:
    numeric_metrics = {
        key: float(value)
        for key, value in metrics.items()
        if isinstance(value, int | float)
    }

    mlflow.log_metrics(numeric_metrics)


def log_artifact_if_exists(path: str | Path) -> None:
    artifact_path = Path(path)

    if artifact_path.exists():
        mlflow.log_artifact(str(artifact_path))
