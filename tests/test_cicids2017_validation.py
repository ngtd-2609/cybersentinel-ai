import numpy as np
import pandas as pd
import pytest

from cybersentinel_ai.validation.cicids2017 import (
    clean_dataframe,
    validate_required_columns,
)


def test_clean_dataframe():
    df = pd.DataFrame(
        {
            " Flow Duration ": [1.0, np.inf],
            " Label ": [" BENIGN ", "Web Attack \ufffd XSS"],
        }
    )

    cleaned = clean_dataframe(df)

    assert list(cleaned.columns) == ["Flow Duration", "Label"]
    assert cleaned["Label"].tolist() == ["BENIGN", "Web Attack - XSS"]
    assert pd.isna(cleaned.loc[1, "Flow Duration"])


def test_validate_required_columns():
    df = pd.DataFrame({"Label": ["BENIGN"]})
    validate_required_columns(df)


def test_validate_required_columns_missing():
    df = pd.DataFrame({"Feature": [1]})

    with pytest.raises(ValueError):
        validate_required_columns(df)
