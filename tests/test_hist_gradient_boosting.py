import numpy as np
import pandas as pd

from cybersentinel_ai.models.hist_gradient_boosting import (
    build_hist_gradient_boosting_classifier,
)


def test_hist_gradient_boosting_fit_predict():
    x = pd.DataFrame(
        {
            "FeatureA": [0.0, 0.1, 0.2, 1.0, 1.1, np.nan],
            "FeatureB": [0.0, 0.2, 0.1, 1.2, 1.0, 1.1],
        }
    )
    y = [0, 0, 0, 1, 1, 1]

    model = build_hist_gradient_boosting_classifier()
    model.fit(x, y)

    predictions = model.predict(x)
    probabilities = model.predict_proba(x)[:, 1]

    assert len(predictions) == len(y)
    assert probabilities.shape == (len(y),)
    assert ((probabilities >= 0.0) & (probabilities <= 1.0)).all()
