import numpy as np
import pandas as pd

from cybersentinel_ai.features.preprocessing import (
    build_numeric_pipeline,
    split_features_target,
)


def test_split_features_target():
    df = pd.DataFrame(
        {
            "FeatureA": [1, 2],
            "FeatureB": [3, 4],
            "Label": ["BENIGN", "DDoS"],
        }
    )

    x, y = split_features_target(df)

    assert list(x.columns) == ["FeatureA", "FeatureB"]
    assert y.tolist() == ["BENIGN", "DDoS"]


def test_numeric_pipeline_handles_nan():
    x = pd.DataFrame(
        {
            "FeatureA": [1.0, np.nan, 3.0],
            "FeatureB": [10.0, 20.0, 30.0],
        }
    )

    pipeline = build_numeric_pipeline()
    transformed = pipeline.fit_transform(x)

    assert transformed.shape == (3, 2)
    assert not np.isnan(transformed).any()
