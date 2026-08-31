import pytest

from cybersentinel_ai.training.multiclass_metrics import (
    multiclass_classification_metrics,
)


def test_multiclass_classification_metrics():
    labels = ["BENIGN", "DDoS", "PortScan"]

    y_true = [
        "BENIGN",
        "BENIGN",
        "DDoS",
        "DDoS",
        "PortScan",
        "PortScan",
    ]

    y_pred = [
        "BENIGN",
        "BENIGN",
        "DDoS",
        "PortScan",
        "PortScan",
        "PortScan",
    ]

    metrics = multiclass_classification_metrics(
        y_true,
        y_pred,
        labels,
    )

    assert metrics["accuracy"] == pytest.approx(5 / 6)
    assert 0.0 <= metrics["macro_f1"] <= 1.0
    assert 0.0 <= metrics["weighted_f1"] <= 1.0
    assert set(metrics["per_class"]) == set(labels)
    assert len(metrics["confusion_matrix"]) == 3
