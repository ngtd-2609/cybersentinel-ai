import pandas as pd
import pytest

from cybersentinel_ai.validation.schema import (
    EXPECTED_FEATURE_COLUMNS,
    validate_cicids2017_schema,
)


def make_valid_dataframe() -> pd.DataFrame:
    data = {
        f"Feature_{i}": [float(i), float(i + 1)]
        for i in range(EXPECTED_FEATURE_COLUMNS)
    }
    data["Label"] = ["BENIGN", "DDoS"]
    return pd.DataFrame(data)


def test_valid_schema():
    df = make_valid_dataframe()
    validate_cicids2017_schema(df)


def test_invalid_column_count():
    df = make_valid_dataframe().drop(columns=["Feature_0"])

    with pytest.raises(ValueError):
        validate_cicids2017_schema(df)


def test_non_numeric_feature():
    df = make_valid_dataframe()
    df["Feature_0"] = ["a", "b"]

    with pytest.raises(ValueError):
        validate_cicids2017_schema(df)
