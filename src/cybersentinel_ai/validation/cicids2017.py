import numpy as np
import pandas as pd


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned.columns = [str(col).strip() for col in cleaned.columns]

    numeric_columns = cleaned.select_dtypes(include=[np.number]).columns
    cleaned[numeric_columns] = cleaned[numeric_columns].replace(
        [np.inf, -np.inf],
        np.nan,
    )

    if "Label" in cleaned.columns:
        cleaned["Label"] = (
            cleaned["Label"]
            .astype(str)
            .str.strip()
            .str.replace("\ufffd", "-", regex=False)
        )

    return cleaned


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: tuple[str, ...] = ("Label",),
) -> None:
    missing = [column for column in required_columns if column not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")
