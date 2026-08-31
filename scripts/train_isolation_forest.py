import json
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from cybersentinel_ai.models.anomaly import build_isolation_forest
from cybersentinel_ai.training.metrics import binary_classification_metrics
from cybersentinel_ai.training.mlflow_utils import (
    configure_mlflow,
    log_artifact_if_exists,
    log_metrics,
)
from cybersentinel_ai.training.thresholds import find_best_f1_threshold

DATA_DIR = Path("data/processed/cicids2017_binary")
ARTIFACT_DIR = Path("artifacts/isolation_forest")
BENIGN_SAMPLE_SIZE = 200_000
RANDOM_STATE = 42
EXPERIMENT_NAME = "cybersentinel-isolation-forest"


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    experiment_id = configure_mlflow(EXPERIMENT_NAME)

    print("Loading train dataset...")
    train = pd.read_parquet(DATA_DIR / "train.parquet")

    benign_train = train[train["Label"] == 0].sample(
        n=min(BENIGN_SAMPLE_SIZE, (train["Label"] == 0).sum()),
        random_state=RANDOM_STATE,
    )

    x_train = benign_train.drop(columns=["Label"])

    print(f"Benign training rows: {len(x_train)}")
    print(f"Features: {x_train.shape[1]}")
    print("Training Isolation Forest...")

    model = build_isolation_forest(random_state=RANDOM_STATE)

    with mlflow.start_run(run_name="isolation-forest") as run:
        params = model.named_steps["model"].get_params()

        mlflow.log_params(
            {
                "model": "IsolationForest",
                "benign_sample_size": len(x_train),
                "random_state": RANDOM_STATE,
                "feature_count": x_train.shape[1],
                "n_estimators": params["n_estimators"],
                "max_samples": params["max_samples"],
                "contamination": params["contamination"],
            }
        )

        model.fit(x_train)

        feature_names = x_train.columns.tolist()

        del train, benign_train, x_train

        print("Loading validation dataset...")
        validation = pd.read_parquet(DATA_DIR / "validation.parquet")

        x_validation = validation[feature_names]
        y_validation = validation["Label"].to_numpy()

        anomaly_scores = -model.decision_function(x_validation)

        best = find_best_f1_threshold(
            y_validation,
            anomaly_scores,
        )
        threshold = best["threshold"]

        predictions = (anomaly_scores >= threshold).astype(int)

        metrics = binary_classification_metrics(
            y_validation,
            predictions,
            anomaly_scores,
        )

        metrics["roc_auc"] = float(
            roc_auc_score(y_validation, anomaly_scores)
        )
        metrics["pr_auc"] = float(
            average_precision_score(y_validation, anomaly_scores)
        )

        bundle_path = ARTIFACT_DIR / "model.joblib"
        metrics_path = ARTIFACT_DIR / "validation_metrics.json"

        joblib.dump(
            {
                "model": model,
                "features": feature_names,
                "threshold": threshold,
            },
            bundle_path,
        )

        result = {
            "threshold_selection": best,
            "validation_metrics": metrics,
        }

        with metrics_path.open("w", encoding="utf-8") as file:
            json.dump(result, file, indent=2)

        log_metrics(metrics)
        mlflow.log_metric("selected_threshold", float(threshold))

        log_artifact_if_exists(bundle_path)
        log_artifact_if_exists(metrics_path)

        mlflow.set_tags(
            {
                "project": "CyberSentinel AI",
                "task": "anomaly detection",
                "dataset": "CIC-IDS2017",
            }
        )

        print("\n=== ISOLATION FOREST VALIDATION ===")
        print(f"threshold: {threshold}")

        for name, value in metrics.items():
            print(f"{name}: {value}")

        print(f"\nMLflow experiment ID: {experiment_id}")
        print(f"MLflow run ID: {run.info.run_id}")
        print(f"Model: {bundle_path}")
        print(f"Metrics: {metrics_path}")


if __name__ == "__main__":
    main()
