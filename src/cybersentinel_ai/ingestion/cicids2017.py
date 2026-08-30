from pathlib import Path

import pandas as pd

DEFAULT_ROOT = Path(
    "/mnt/d/CyberSentinel_AI/datasets/CIC-IDS2017/MachineLearningCVE"
)


def list_csv_files(root: Path = DEFAULT_ROOT) -> list[Path]:
    return sorted(root.glob("*.csv"))


def normalize_columns(columns) -> list[str]:
    return [str(col).strip() for col in columns]


def read_cicids_csv(path: Path, **kwargs) -> pd.DataFrame:
    df = pd.read_csv(path, **kwargs)
    df.columns = normalize_columns(df.columns)

    if "Label" in df.columns:
        df["Label"] = (
            df["Label"]
            .astype(str)
            .str.strip()
            .str.replace("\ufffd", "-", regex=False)
        )

    return df
