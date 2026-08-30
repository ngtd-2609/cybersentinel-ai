import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def split_features_target(
    df: pd.DataFrame,
    target_column: str = "Label",
) -> tuple[pd.DataFrame, pd.Series]:
    if target_column not in df.columns:
        raise ValueError(f"Missing target column: {target_column}")

    x = df.drop(columns=[target_column])
    y = df[target_column]

    return x, y


def build_numeric_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
