import pytest

from cybersentinel_ai.features.splitting import (
    binary_split_for_file,
    to_binary_label,
)


def test_binary_split_for_file():
    assert binary_split_for_file("Monday-WorkingHours.pcap_ISCX.csv") == "train"
    assert (
        binary_split_for_file(
            "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv"
        )
        == "validation"
    )
    assert (
        binary_split_for_file("Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv")
        == "test"
    )


def test_binary_split_unknown_file():
    with pytest.raises(ValueError):
        binary_split_for_file("unknown.csv")


def test_to_binary_label():
    assert to_binary_label(" BENIGN ") == "BENIGN"
    assert to_binary_label("DDoS") == "ATTACK"
    assert to_binary_label("Web Attack - XSS") == "ATTACK"
