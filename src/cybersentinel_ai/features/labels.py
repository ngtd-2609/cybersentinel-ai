import re

CANONICAL_LABELS = (
    "BENIGN",
    "Bot",
    "DDoS",
    "DoS GoldenEye",
    "DoS Hulk",
    "DoS Slowhttptest",
    "DoS slowloris",
    "FTP-Patator",
    "Heartbleed",
    "Infiltration",
    "PortScan",
    "SSH-Patator",
    "Web Attack - Brute Force",
    "Web Attack - Sql Injection",
    "Web Attack - XSS",
)


def normalize_attack_label(label: str) -> str:
    normalized = str(label).strip().replace("\ufffd", "-")
    normalized = re.sub(r"\s+", " ", normalized)

    if normalized.startswith("Web Attack"):
        normalized = re.sub(
            r"^Web Attack\s*-\s*",
            "Web Attack - ",
            normalized,
        )

    if normalized not in CANONICAL_LABELS:
        raise ValueError(f"Unknown CIC-IDS2017 label: {normalized}")

    return normalized
