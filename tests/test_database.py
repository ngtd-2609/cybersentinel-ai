from sqlalchemy import text

from cybersentinel_ai.db.database import build_engine


def test_sqlite_database_connection():
    engine = build_engine("sqlite:///:memory:")

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar_one()

    assert result == 1


def test_sqlite_foreign_keys_are_enabled():
    engine = build_engine("sqlite:///:memory:")

    with engine.connect() as connection:
        enabled = connection.execute(text("PRAGMA foreign_keys")).scalar_one()

    assert enabled == 1
