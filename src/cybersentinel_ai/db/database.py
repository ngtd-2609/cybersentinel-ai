import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_DATABASE_URL = "sqlite:///./cybersentinel.db"


def build_engine(database_url: str):
    connect_args = {}

    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )


DATABASE_URL = os.getenv(
    "CYBERSENTINEL_DATABASE_URL",
    DEFAULT_DATABASE_URL,
)

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


def create_tables() -> None:
    from cybersentinel_ai.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
