from collections import Counter
from pathlib import Path

import pandas as pd

from cybersentinel_ai.features.splitting import split_for_file

DATA_ROOT = Path(
    "/mnt/d/CyberSentinel_AI/datasets/CIC-IDS2017/MachineLearningCVE"
)


def main() -> None:
    counts = {
        "train": Counter(),
        "validation": Counter(),
        "test": Counter(),
    }

    for path in sorted(DATA_ROOT.glob("*.csv")):
        split = split_for_file(path)

        for chunk in pd.read_csv(path, usecols=[" Label"], chunksize=100_000):
            labels = chunk[" Label"].astype(str).str.strip()
            counts[split].update(labels.value_counts().to_dict())

    for split, labels in counts.items():
        print(f"\n=== {split.upper()} ===")
        print("rows:", sum(labels.values()))
        print("labels:", len(labels))

        for label, count in labels.most_common():
            print(f"{label}: {count}")

    train_labels = set(counts["train"])

    print("\n=== LABELS NOT PRESENT IN TRAIN ===")
    print("validation:", sorted(set(counts["validation"]) - train_labels))
    print("test:", sorted(set(counts["test"]) - train_labels))


if __name__ == "__main__":
    main()
