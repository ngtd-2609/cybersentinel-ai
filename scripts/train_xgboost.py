import json
from pathlib import Path

import joblib
import mlflow
import pandas as pd

from cybersentinel_ai.models.xgboost_model import build_xgboost_classifier
from cybersentinel_ai.training.metrics import binary_classification_metrics
from cybersentinel_ai.training.mlflow_utils import (
    configure_mlflow,
    log_artifact_if_exists,
    log_metrics,
)

DATA_DIR = Path("data/processed/cicids2017_binary")
ARTIFACT_DIR = Path("artifacts/xgboost")
TRAIN_SAMPLE_SIZE = 400_000
RANDOM_STATE = 42
EXPERIMENT_NAME = "cybersentinel-binary-xgboost"


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    experiment_id = configure_mlflow(EXPERIMENT_NAME)

    print("Loading train dataset...")
    train = pd.read_parquet(DATA_DIR / "train.parquet")

    attack = train[train["Label"] == 1].sample(
        n=TRAIN_SAMPLE_SIZE // 2,
        random_state=RANDOM_STATE,
    )
    benign = train[train["Label"] == 0].sample(
        n=TRAIN_SAMPLE_SIZE // 2,
        random_state=RANDOM_STATE,
    )

    train_sample = (
        pd.concat([benign, attack], ignore_index=True)
        .sample(frac=1.0, random_state=RANDOM_STATE)
        .reset_index(drop=True)
    )

    del train, benign, attack

    x_train = train_sample.drop(columns=["Label"])
    y_train = train_sample["Label"]

    print(f"Training rows: {len(train_sample)}")
    print(f"Features: {x_train.shape[1]}")
    print(f"BENIGN: {(y_train == 0).sum()}")
    print(f"ATTACK: {(y_train == 1).sum()}")
    print("Training XGBoost model...")

    model = build_xgboost_classifier(random_state=RANDOM_STATE)

    with mlflow.start_run(run_name="xgboost-binary") as run:
        mlflow.log_params(
            {
                "model": "XGBClassifier",
                "train_sample_size": TRAIN_SAMPLE_SIZE,
                "random_state": RANDOM_STATE,
                "feature_count": x_train.shape[1],
                "n_estimators": model.get_params()["n_estimators"],
                "max_depth": model.get_params()["max_depth"],
                "learning_rate": model.get_params()["learning_rate"],
                "subsample": model.get_params()["subsample"],
                "colsample_bytree": model.get_params()["colsample_bytree"],
                "min_child_weight": model.get_params()["min_child_weight"],
                "reg_lambda": model.get_params()["reg_lambda"],
            }
        )

        model.fit(x_train, y_train)

        del train_sample, x_train, y_train

        print("Loading validation dataset...")
        validation = pd.read_parquet(DATA_DIR / "validation.parquet")

        x_validation = validation.drop(columns=["Label"])
        y_validation = validation["Label"]

        print("Evaluating...")
        y_pred = model.predict(x_validation)
        y_score = model.predict_proba(x_validation)[:, 1]

        metrics = binary_classification_metrics(
            y_validation,
            y_pred,
            y_score,
        )

        model_path = ARTIFACT_DIR / "model.joblib"
        metrics_path = ARTIFACT_DIR / "validation_metrics.json"

        joblib.dump(model, model_path)

        with metrics_path.open("w", encoding="utf-8") as file:
            json.dump(metrics, file, indent=2)

        log_metrics(metrics)
        log_artifact_if_exists(model_path)
        log_artifact_if_exists(metrics_path)

        mlflow.set_tags(
            {
                "project": "CyberSentinel AI",
                "task": "binary intrusion classification",
                "dataset": "CIC-IDS2017",
            }
        )

        print("\n=== VALIDATION METRICS ===")

        for name, value in metrics.items():
            print(f"{name}: {value}")

        print(f"\nMLflow experiment ID: {experiment_id}")
        print(f"MLflow run ID: {run.info.run_id}")
        print(f"Model: {model_path}")
        print(f"Metrics: {metrics_path}")


if __name__ == "__main__":
    main()
