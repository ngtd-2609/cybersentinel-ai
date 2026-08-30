import pytest

from cybersentinel_ai.training.metrics import binary_classification_metrics


def test_binary_classification_metrics():
    y_true = [0, 0, 1, 1]
    y_pred = [0, 1, 1, 1]
    y_score = [0.1, 0.7, 0.8, 0.9]

    metrics = binary_classification_metrics(y_true, y_pred, y_score)

    assert metrics["tn"] == 1
    assert metrics["fp"] == 1
    assert metrics["fn"] == 0
    assert metrics["tp"] == 2
    assert metrics["recall"] == pytest.approx(1.0)
    assert metrics["precision"] == pytest.approx(2 / 3)
    assert 0.0 <= metrics["roc_auc"] <= 1.0
    assert 0.0 <= metrics["pr_auc"] <= 1.0
