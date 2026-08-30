import pytest

from cybersentinel_ai.training.thresholds import find_best_f1_threshold


def test_find_best_f1_threshold():
    y_true = [0, 0, 1, 1]
    y_score = [0.1, 0.4, 0.6, 0.9]

    result = find_best_f1_threshold(y_true, y_score)

    assert 0.0 < result["threshold"] < 1.0
    assert result["f1"] == pytest.approx(1.0)
    assert result["precision"] == pytest.approx(1.0)
    assert result["recall"] == pytest.approx(1.0)
