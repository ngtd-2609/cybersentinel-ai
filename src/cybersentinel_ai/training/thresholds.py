import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score


def find_best_f1_threshold(
    y_true,
    y_score,
    thresholds: np.ndarray | None = None,
) -> dict[str, float]:
    if thresholds is None:
        thresholds = np.linspace(0.001, 0.999, 999)

    best = {
        "threshold": 0.5,
        "f1": -1.0,
        "precision": 0.0,
        "recall": 0.0,
    }

    for threshold in thresholds:
        y_pred = (np.asarray(y_score) >= threshold).astype(int)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        if f1 > best["f1"]:
            best = {
                "threshold": float(threshold),
                "f1": float(f1),
                "precision": float(
                    precision_score(y_true, y_pred, zero_division=0)
                ),
                "recall": float(
                    recall_score(y_true, y_pred, zero_division=0)
                ),
            }

    return best
