import pandas as pd

from cybersentinel_ai.features.selection import (
    FEATURES_TO_DROP,
    drop_unusable_features,
)


def test_drop_unusable_features():
    df = pd.DataFrame(
        {
            "Flow Duration": [1, 2],
            "Fwd Header Length.1": [10, 20],
            "Bwd PSH Flags": [0, 0],
            "Label": ["BENIGN", "DDoS"],
        }
    )

    result = drop_unusable_features(df)

    assert list(result.columns) == ["Flow Duration", "Label"]


def test_expected_drop_feature_count():
    assert len(FEATURES_TO_DROP) == 11
    assert len(set(FEATURES_TO_DROP)) == 11
