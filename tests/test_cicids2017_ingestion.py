from pathlib import Path

from cybersentinel_ai.ingestion.cicids2017 import normalize_columns


def test_normalize_columns():
    columns = [" Flow Duration", " Label "]
    assert normalize_columns(columns) == ["Flow Duration", "Label"]


def test_dataset_root_exists():
    root = Path("/mnt/d/CyberSentinel_AI/datasets/CIC-IDS2017/MachineLearningCVE")
    assert root.exists()
    assert len(list(root.glob("*.csv"))) == 8
