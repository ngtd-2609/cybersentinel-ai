import json
from pathlib import Path

import joblib
import pandas as pd

from cybersentinel_ai.models.baseline import build_baseline_classifier
from cybersentinel_ai.training.metrics import binary_classification_metrics

DATA_DIR = Path("data/processed/cicids2017_binary")
ARTIFACT_DIR = Path("artifacts/baseline")
TRAIN_SAMPLE_SIZE = 400_000
RANDOM_STATE = 42


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading train dataset...")
    train = pd.read_parquet(DATA_DIR / "train.parquet")

    train_sample = (
        train.groupby("Label", group_keys=False)
        .sample(
            n=min(
                TRAIN_SAMPLE_SIZE // train["Label"].nunique(),
                train["Label"].value_counts().min(),
            ),
            random_state=RANDOM_STATE,
        )
        .sample(frac=1.0, random_state=RANDOM_STATE)
        .reset_index(drop=True)
    )

    del train

    x_train = train_sample.drop(columns=["Label"])
    y_train = train_sample["Label"]

    print(f"Training rows: {len(train_sample)}")
    print(f"Features: {x_train.shape[1]}")
    print("Training baseline model...")

    model = build_baseline_classifier(random_state=RANDOM_STATE)
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

    print("\n=== VALIDATION METRICS ===")

    for name, value in metrics.items():
        print(f"{name}: {value}")

    print(f"\nModel: {model_path}")
    print(f"Metrics: {metrics_path}")


if __name__ == "__main__":
    main()
