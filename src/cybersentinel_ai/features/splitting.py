from pathlib import Path

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
