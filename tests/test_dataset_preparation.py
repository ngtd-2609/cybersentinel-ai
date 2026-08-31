import numpy as np
import pandas as pd

from cybersentinel_ai.features.dataset import prepare_binary_dataframe


def test_prepare_binary_dataframe():
    df = pd.DataFrame(
        {
            " Flow Duration ": [10.0, np.inf],
            " Fwd Header Length.1 ": [20, 30],
            " Bwd PSH Flags ": [0, 0],
            " Label ": [" BENIGN ", "DDoS"],
        }
    )

    prepared = prepare_binary_dataframe(df)

    assert list(prepared.columns) == ["Flow Duration", "Label"]
    assert prepared["Label"].tolist() == [0, 1]
    assert prepared["Label"].dtype == "int8"
    assert pd.isna(prepared.loc[1, "Flow Duration"])


def test_prepare_multiclass_dataframe():
    from cybersentinel_ai.features.dataset import prepare_multiclass_dataframe

    df = pd.DataFrame(
        {
            " Flow Duration ": [10.0, 20.0],
            " Fwd Header Length.1 ": [30, 40],
            " Bwd PSH Flags ": [0, 0],
            " Label ": [" BENIGN ", "Web Attack \ufffd XSS"],
        }
    )

    prepared = prepare_multiclass_dataframe(df)

    assert list(prepared.columns) == ["Flow Duration", "Label"]
    assert prepared["Label"].tolist() == [
        "BENIGN",
        "Web Attack - XSS",
    ]
