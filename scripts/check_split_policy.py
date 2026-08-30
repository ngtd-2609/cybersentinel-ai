from collections import Counter

import pandas as pd

from cybersentinel_ai.features.splitting import (
    binary_split_for_file,
    to_binary_label,
)
from cybersentinel_ai.ingestion.cicids2017 import get_dataset_root

DATA_ROOT = get_dataset_root()


def main() -> None:
    counts = {
        "train": Counter(),
        "validation": Counter(),
        "test": Counter(),
    }

    for path in sorted(DATA_ROOT.glob("*.csv")):
        split = binary_split_for_file(path)

        for chunk in pd.read_csv(path, usecols=[" Label"], chunksize=100_000):
            labels = chunk[" Label"].astype(str).map(to_binary_label)
            counts[split].update(labels.value_counts().to_dict())

    for split, labels in counts.items():
        total = sum(labels.values())

        print(f"\n=== {split.upper()} ===")
        print(f"rows: {total}")

        for label, count in labels.most_common():
            percentage = count / total * 100
            print(f"{label}: {count} ({percentage:.2f}%)")

        if set(labels) != {"BENIGN", "ATTACK"}:
            raise ValueError(f"{split} does not contain both binary classes")

    print("\nPASS | All splits contain BENIGN and ATTACK")


if __name__ == "__main__":
    main()
