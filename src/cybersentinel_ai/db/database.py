from collections.abc import Generator, Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from cybersentinel_ai.core.config import get_settings


def build_engine(database_url: str):
    connect_args = {}

    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    database_engine = create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )

    if database_url.startswith("sqlite"):
        @event.listens_for(database_engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return database_engine


DATABASE_URL = get_settings().database_url

engine = build_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()

    try:
        yield database
    finally:
        database.close()


@contextmanager
def atomic(database: Session) -> Iterator[None]:
    """Commit one business action or roll all of it back."""
    try:
        yield
        database.commit()
    except BaseException:
        database.rollback()
        raise


def create_tables() -> None:
    from cybersentinel_ai.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
