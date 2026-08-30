import json
from pathlib import Path

import joblib
import pandas as pd

from cybersentinel_ai.training.metrics import binary_classification_metrics
from cybersentinel_ai.training.thresholds import find_best_f1_threshold

DATA_DIR = Path("data/processed/cicids2017_binary")
MODEL_PATH = Path("artifacts/xgboost/model.joblib")
OUTPUT_PATH = Path("artifacts/xgboost/test_metrics.json")


def main() -> None:
    model = joblib.load(MODEL_PATH)

    print("Loading validation dataset...")
    validation = pd.read_parquet(DATA_DIR / "validation.parquet")

    x_validation = validation.drop(columns=["Label"])
    y_validation = validation["Label"]
    validation_scores = model.predict_proba(x_validation)[:, 1]

    best = find_best_f1_threshold(
        y_validation,
        validation_scores,
    )
    threshold = best["threshold"]

    print(f"Selected validation threshold: {threshold}")

    del validation, x_validation, y_validation, validation_scores

    print("Loading locked test dataset...")
    test = pd.read_parquet(DATA_DIR / "test.parquet")

    x_test = test.drop(columns=["Label"])
    y_test = test["Label"]

    test_scores = model.predict_proba(x_test)[:, 1]
    test_predictions = (test_scores >= threshold).astype(int)

    metrics = binary_classification_metrics(
        y_test,
        test_predictions,
        test_scores,
    )

    result = {
        "selected_threshold": threshold,
        "validation_threshold_metrics": best,
        "test_metrics": metrics,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    print("\n=== LOCKED TEST METRICS ===")

    for name, value in metrics.items():
        print(f"{name}: {value}")

    print(f"\nMetrics: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
