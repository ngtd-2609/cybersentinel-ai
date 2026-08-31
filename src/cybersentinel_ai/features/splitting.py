from pathlib import Path

import numpy as np
import pandas as pd

BINARY_TRAIN_FILES = {
    "Monday-WorkingHours.pcap_ISCX.csv",
    "Tuesday-WorkingHours.pcap_ISCX.csv",
    "Wednesday-workingHours.pcap_ISCX.csv",
}

BINARY_VALIDATION_FILES = {
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
    "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv",
}

BINARY_TEST_FILES = {
    "Friday-WorkingHours-Morning.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
}


def binary_split_for_file(path: str | Path) -> str:
    name = Path(path).name

    if name in BINARY_TRAIN_FILES:
        return "train"
    if name in BINARY_VALIDATION_FILES:
        return "validation"
    if name in BINARY_TEST_FILES:
        return "test"

    raise ValueError(f"Unknown CIC-IDS2017 file: {name}")


def to_binary_label(label: str) -> str:
    normalized = str(label).strip()
    return "BENIGN" if normalized == "BENIGN" else "ATTACK"


def multiclass_split_masks(
    df: pd.DataFrame,
    train_percent: int = 80,
    validation_percent: int = 10,
):
    if train_percent + validation_percent >= 100:
        raise ValueError("train + validation percentage must be < 100")

    if "Label" not in df.columns:
        raise ValueError("Missing Label column")

    train_mask = np.zeros(len(df), dtype=bool)
    validation_mask = np.zeros(len(df), dtype=bool)
    test_mask = np.zeros(len(df), dtype=bool)

    labels = df["Label"].to_numpy()

    for label in sorted(df["Label"].unique()):
        indices = np.flatnonzero(labels == label)
        subset = df.iloc[indices]

        hashes = pd.util.hash_pandas_object(
            subset,
            index=False,
        ).to_numpy(dtype="uint64")

        unique_hashes = np.unique(hashes)
        unique_hashes.sort()

        group_count = len(unique_hashes)

        if group_count >= 3:
            validation_count = max(
                1,
                round(group_count * validation_percent / 100),
            )
            test_count = max(
                1,
                round(
                    group_count
                    * (100 - train_percent - validation_percent)
                    / 100
                ),
            )

            while validation_count + test_count >= group_count:
                if validation_count >= test_count and validation_count > 1:
                    validation_count -= 1
                elif test_count > 1:
                    test_count -= 1
                else:
                    break

            train_count = group_count - validation_count - test_count
        elif group_count == 2:
            train_count = 1
            validation_count = 0
            test_count = 1
        else:
            train_count = 1
            validation_count = 0
            test_count = 0

        train_hashes = set(unique_hashes[:train_count])
        validation_hashes = set(
            unique_hashes[
                train_count : train_count + validation_count
            ]
        )
        test_hashes = set(
            unique_hashes[train_count + validation_count :]
        )

        for local_index, row_hash in enumerate(hashes):
            global_index = indices[local_index]

            if row_hash in train_hashes:
                train_mask[global_index] = True
            elif row_hash in validation_hashes:
                validation_mask[global_index] = True
            elif row_hash in test_hashes:
                test_mask[global_index] = True

    return train_mask, validation_mask, test_mask
