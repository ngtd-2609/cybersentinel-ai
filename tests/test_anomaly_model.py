import numpy as np
import pandas as pd

from cybersentinel_ai.models.anomaly import build_isolation_forest


def test_isolation_forest_fit_score():
    x = pd.DataFrame(
        {
            "FeatureA": [0.0, 0.1, 0.2, 0.1, np.nan, 10.0],
            "FeatureB": [0.0, 0.2, 0.1, 0.3, 0.2, 10.0],
        }
    )

    model = build_isolation_forest()
    model.fit(x)

    scores = model.decision_function(x)
    predictions = model.predict(x)

    assert scores.shape == (len(x),)
    assert predictions.shape == (len(x),)
    assert set(predictions).issubset({-1, 1})
