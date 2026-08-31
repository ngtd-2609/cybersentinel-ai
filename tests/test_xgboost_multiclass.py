import numpy as np
import pandas as pd

from cybersentinel_ai.models.xgboost_multiclass import (
    build_xgboost_multiclass_classifier,
)


def test_xgboost_multiclass_fit_predict():
    x = pd.DataFrame(
        {
            "FeatureA": [0.0, 0.1, 1.0, 1.1, 2.0, np.nan],
            "FeatureB": [0.0, 0.2, 1.0, 1.2, 2.0, 2.1],
        }
    )
    y = [0, 0, 1, 1, 2, 2]

    model = build_xgboost_multiclass_classifier(num_class=3)
    model.fit(x, y)

    predictions = model.predict(x)
    probabilities = model.predict_proba(x)

    assert len(predictions) == len(y)
    assert probabilities.shape == (len(y), 3)
    assert np.allclose(probabilities.sum(axis=1), 1.0)
