import pytest

from cybersentinel_ai.features.labels import (
    CANONICAL_LABELS,
    normalize_attack_label,
)


def test_all_canonical_labels_unique():
    assert len(CANONICAL_LABELS) == 15
    assert len(set(CANONICAL_LABELS)) == 15


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (" BENIGN ", "BENIGN"),
        ("DDoS", "DDoS"),
        ("Web Attack \ufffd Brute Force", "Web Attack - Brute Force"),
        ("Web Attack - XSS", "Web Attack - XSS"),
        ("Web Attack   -   Sql Injection", "Web Attack - Sql Injection"),
    ],
)
def test_normalize_attack_label(raw, expected):
    assert normalize_attack_label(raw) == expected


def test_unknown_label():
    with pytest.raises(ValueError):
        normalize_attack_label("Unknown Attack")
