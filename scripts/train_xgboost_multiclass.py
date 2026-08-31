import json
from pathlib import Path

import joblib
import pandas as pd

from cybersentinel_ai.features.labels import CANONICAL_LABELS
from cybersentinel_ai.models.xgboost_multiclass import (
    build_xgboost_multiclass_classifier,
)
from cybersentinel_ai.training.multiclass_metrics import (
    multiclass_classification_metrics,
)

DATA_DIR = Path("data/processed/cicids2017_multiclass")
ARTIFACT_DIR = Path("artifacts/xgboost_multiclass")
MAX_ROWS_PER_CLASS = 50_000
RANDOM_STATE = 42


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    label_to_id = {
        label: index
        for index, label in enumerate(CANONICAL_LABELS)
    }
    id_to_label = dict(enumerate(CANONICAL_LABELS))

    print("Loading train dataset...")
    train = pd.read_parquet(DATA_DIR / "train.parquet")

    sampled_parts = []

    for label, group in train.groupby("Label"):
        sample_size = min(len(group), MAX_ROWS_PER_CLASS)
        sampled = group.sample(
            n=sample_size,
            random_state=RANDOM_STATE,
        )
        sampled_parts.append(sampled)

        print(
            f"{label}: original={len(group)} "
            f"training={sample_size}"
        )

    train_sample = (
        pd.concat(sampled_parts, ignore_index=True)
        .sample(frac=1.0, random_state=RANDOM_STATE)
        .reset_index(drop=True)
    )

    del train, sampled_parts

    x_train = train_sample.drop(columns=["Label"])
    y_train = train_sample["Label"].map(label_to_id).astype("int32")

    print(f"\nTraining rows: {len(train_sample)}")
    print(f"Features: {x_train.shape[1]}")
    print(f"Classes: {y_train.nunique()}")
    print("Training multiclass XGBoost...")

    model = build_xgboost_multiclass_classifier(
        num_class=len(CANONICAL_LABELS),
        random_state=RANDOM_STATE,
    )
    model.fit(x_train, y_train)

    feature_names = x_train.columns.tolist()

    del train_sample, x_train, y_train

    print("Loading validation dataset...")
    validation = pd.read_parquet(DATA_DIR / "validation.parquet")

    x_validation = validation.drop(columns=["Label"])
    y_validation = validation["Label"].tolist()

    predictions = model.predict(x_validation)
    predicted_labels = [
        id_to_label[int(prediction)]
        for prediction in predictions
    ]

    metrics = multiclass_classification_metrics(
        y_validation,
        predicted_labels,
        list(CANONICAL_LABELS),
    )

    bundle_path = ARTIFACT_DIR / "model.joblib"
    metrics_path = ARTIFACT_DIR / "validation_metrics.json"

    joblib.dump(
        {
            "model": model,
            "labels": list(CANONICAL_LABELS),
            "features": feature_names,
        },
        bundle_path,
    )

    with metrics_path.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)

    print("\n=== MULTICLASS VALIDATION ===")
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

    print(f"\nModel: {bundle_path}")
    print(f"Metrics: {metrics_path}")


if __name__ == "__main__":
    main()
