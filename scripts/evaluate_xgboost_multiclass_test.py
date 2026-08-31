import json
from pathlib import Path

import joblib
import pandas as pd

from cybersentinel_ai.features.labels import CANONICAL_LABELS
from cybersentinel_ai.training.multiclass_metrics import (
    multiclass_classification_metrics,
)

DATA_PATH = Path("data/processed/cicids2017_multiclass/test.parquet")
MODEL_PATH = Path("artifacts/xgboost_multiclass/model.joblib")
OUTPUT_PATH = Path("artifacts/xgboost_multiclass/test_metrics.json")


def main() -> None:
    print("Loading model...")
    bundle = joblib.load(MODEL_PATH)

    model = bundle["model"]
    labels = bundle["labels"]
    features = bundle["features"]

    if labels != list(CANONICAL_LABELS):
        raise ValueError("Model labels do not match canonical labels")

    print("Loading locked multiclass test dataset...")
    test = pd.read_parquet(DATA_PATH)

    x_test = test[features]
    y_test = test["Label"].tolist()

    print("Evaluating locked test set...")
    predictions = model.predict(x_test)

    predicted_labels = [
        labels[int(prediction)]
        for prediction in predictions
    ]

    metrics = multiclass_classification_metrics(
        y_test,
        predicted_labels,
        labels,
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)

    print("\n=== LOCKED MULTICLASS TEST ===")
    print(f"accuracy: {metrics['accuracy']}")
    print(f"macro_f1: {metrics['macro_f1']}")
    print(f"weighted_f1: {metrics['weighted_f1']}")

    print("\n=== PER CLASS ===")

    for label, values in metrics["per_class"].items():
        print(
            f"{label}: "
            f"precision={values['precision']:.6f} "
            f"recall={values['recall']:.6f} "
            f"f1={values['f1']:.6f} "
            f"support={values['support']}"
        )

    print(f"\nMetrics: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
