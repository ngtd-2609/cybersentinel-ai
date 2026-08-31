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


def test_multiclass_split_masks_keep_duplicates_together():
    import pandas as pd

    from cybersentinel_ai.features.splitting import multiclass_split_masks

    df = pd.DataFrame(
        {
            "FeatureA": [1, 1, 2, 3, 4],
            "FeatureB": [10, 10, 20, 30, 40],
            "Label": ["BENIGN", "BENIGN", "DDoS", "Bot", "PortScan"],
        }
    )

    train, validation, test = multiclass_split_masks(df)

    memberships = []

    for i in range(len(df)):
        memberships.append(
            (
                bool(train[i]),
                bool(validation[i]),
                bool(test[i]),
            )
        )

    assert memberships[0] == memberships[1]
    assert all(sum(item) == 1 for item in memberships)


def test_multiclass_split_masks_deterministic():
    import pandas as pd

    from cybersentinel_ai.features.splitting import multiclass_split_masks

    df = pd.DataFrame(
        {
            "Feature": list(range(100)),
            "Label": ["BENIGN"] * 100,
        }
    )

    first = multiclass_split_masks(df)
    second = multiclass_split_masks(df)

    for first_mask, second_mask in zip(first, second, strict=True):
        assert (first_mask == second_mask).all()


def test_multiclass_split_keeps_rare_class_in_all_splits():
    import pandas as pd

    from cybersentinel_ai.features.splitting import multiclass_split_masks

    df = pd.DataFrame(
        {
            "Feature": list(range(11)) + list(range(100, 120)),
            "Label": ["Rare"] * 11 + ["Common"] * 20,
        }
    )

    train, validation, test = multiclass_split_masks(df)

    for label in ["Rare", "Common"]:
        label_mask = df["Label"].eq(label).to_numpy()

        assert (train & label_mask).any()
        assert (validation & label_mask).any()
        assert (test & label_mask).any()
