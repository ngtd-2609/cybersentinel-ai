from pathlib import Path

from cybersentinel_ai.ingestion.cicids2017 import (
    get_dataset_root,
    list_csv_files,
    normalize_columns,
)


def test_normalize_columns():
    columns = [" Flow Duration", " Label "]
    assert normalize_columns(columns) == ["Flow Duration", "Label"]


def test_list_csv_files(tmp_path: Path):
    (tmp_path / "b.csv").touch()
    (tmp_path / "a.csv").touch()
    (tmp_path / "ignore.txt").touch()

    files = list_csv_files(tmp_path)

    assert [path.name for path in files] == ["a.csv", "b.csv"]


def test_dataset_root_from_environment(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("CYBERSENTINEL_CICIDS2017_ROOT", str(tmp_path))
    assert get_dataset_root() == tmp_path
