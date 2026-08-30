from pathlib import Path

import pandas as pd

from cybersentinel_ai.validation.schema import validate_cicids2017_schema

DATA_ROOT = Path(
    "/mnt/d/CyberSentinel_AI/datasets/CIC-IDS2017/MachineLearningCVE"
)


def main() -> None:
    for path in sorted(DATA_ROOT.glob("*.csv")):
        df = pd.read_csv(path, nrows=10_000)
        df.columns = [str(column).strip() for column in df.columns]

        validate_cicids2017_schema(df)

        print(f"PASS | {path.name} | rows_checked={len(df)} | columns={len(df.columns)}")


if __name__ == "__main__":
    main()
