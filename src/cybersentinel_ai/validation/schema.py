import pandas as pd

TARGET_COLUMN = "Label"
EXPECTED_TOTAL_COLUMNS = 79
EXPECTED_FEATURE_COLUMNS = 78


def validate_cicids2017_schema(df: pd.DataFrame) -> None:
    if len(df.columns) != EXPECTED_TOTAL_COLUMNS:
        raise ValueError(
            f"Expected {EXPECTED_TOTAL_COLUMNS} columns, got {len(df.columns)}"
        )

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing target column: {TARGET_COLUMN}")

    feature_columns = df.drop(columns=[TARGET_COLUMN]).columns

    if len(feature_columns) != EXPECTED_FEATURE_COLUMNS:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COLUMNS} feature columns, "
            f"got {len(feature_columns)}"
        )

    non_numeric = [
        column
        for column in feature_columns
        if not pd.api.types.is_numeric_dtype(df[column])
    ]

    if non_numeric:
        raise ValueError(f"Non-numeric feature columns: {non_numeric}")
