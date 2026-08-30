import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

DATA_ROOT = Path(
    "/mnt/d/CyberSentinel_AI/datasets/CIC-IDS2017/MachineLearningCVE"
)
OUTPUT_PATH = Path("docs/data_audit_cicids2017.json")


def main() -> None:
    files = sorted(DATA_ROOT.glob("*.csv"))
    reference_columns = None
    report = {
        "dataset": "CIC-IDS2017",
        "file_count": len(files),
        "total_rows": 0,
        "labels": {},
        "files": [],
    }

    total_labels = Counter()

    for path in files:
        rows = 0
        nan_count = 0
        inf_count = 0
        labels = Counter()
        file_columns = None

        for chunk in pd.read_csv(path, chunksize=100_000):
            chunk.columns = [str(col).strip() for col in chunk.columns]

            if file_columns is None:
                file_columns = chunk.columns.tolist()

            if reference_columns is None:
                reference_columns = file_columns

            if "Label" in chunk.columns:
                chunk["Label"] = (
                    chunk["Label"]
                    .astype(str)
                    .str.strip()
                    .str.replace("\ufffd", "-", regex=False)
                )
                labels.update(chunk["Label"].value_counts().to_dict())

            rows += len(chunk)
            nan_count += int(chunk.isna().sum().sum())

            numeric = chunk.select_dtypes(include=[np.number])
            inf_count += int(np.isinf(numeric).sum().sum())

        total_labels.update(labels)
        report["total_rows"] += rows

        report["files"].append(
            {
                "name": path.name,
                "size_bytes": path.stat().st_size,
                "rows": rows,
                "columns": len(file_columns or []),
                "schema_matches_reference": file_columns == reference_columns,
                "nan_cells": nan_count,
                "inf_cells": inf_count,
                "labels": dict(labels),
            }
        )

    report["labels"] = dict(total_labels)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Report written: {OUTPUT_PATH}")
    print(f"Files: {report['file_count']}")
    print(f"Rows: {report['total_rows']}")
    print(f"Labels: {len(report['labels'])}")


if __name__ == "__main__":
    main()
