import pandas as pd

from cybersentinel_ai.features.selection import drop_unusable_features
from cybersentinel_ai.features.splitting import to_binary_label
from cybersentinel_ai.validation.cicids2017 import clean_dataframe


def prepare_binary_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    prepared = clean_dataframe(df)
    prepared = drop_unusable_features(prepared)

    if "Label" not in prepared.columns:
        raise ValueError("Missing target column: Label")

    prepared["Label"] = (
        prepared["Label"]
        .map(to_binary_label)
        .map({"BENIGN": 0, "ATTACK": 1})
        .astype("int8")
    )

    return prepared
