import pandas as pd

DUPLICATE_FEATURES = (
    "Fwd Header Length.1",
)

TRAIN_CONSTANT_FEATURES = (
    "Bwd PSH Flags",
    "Fwd URG Flags",
    "Bwd URG Flags",
    "CWE Flag Count",
    "Fwd Avg Bytes/Bulk",
    "Fwd Avg Packets/Bulk",
    "Fwd Avg Bulk Rate",
    "Bwd Avg Bytes/Bulk",
    "Bwd Avg Packets/Bulk",
    "Bwd Avg Bulk Rate",
)

FEATURES_TO_DROP = DUPLICATE_FEATURES + TRAIN_CONSTANT_FEATURES


def drop_unusable_features(df: pd.DataFrame) -> pd.DataFrame:
    existing = [column for column in FEATURES_TO_DROP if column in df.columns]
    return df.drop(columns=existing)
