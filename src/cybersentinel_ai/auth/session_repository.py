from sqlalchemy import select
from sqlalchemy.orm import Session

from cybersentinel_ai.db.models import UserSession


def create_user_session(db: Session, session: UserSession) -> UserSession:
    db.add(session)
    db.flush()
    db.refresh(session)
    return session


def get_user_session(
    db: Session,
    session_id: str,
    *,
    for_update: bool = False,
) -> UserSession | None:
    statement = select(UserSession).where(UserSession.id == session_id)
    if for_update:
        statement = statement.with_for_update()
    return db.scalar(statement)


def get_user_session_by_refresh_hash(
    db: Session,
    refresh_token_hash: str,
    *,
    for_update: bool = False,
) -> UserSession | None:
    statement = select(UserSession).where(
        UserSession.refresh_token_hash == refresh_token_hash
    )
    if for_update:
        statement = statement.with_for_update()
    return db.scalar(statement)


def get_user_sessions(
    db: Session,
    user_id: int,
    *,
    for_update: bool = False,
) -> list[UserSession]:
    statement = select(UserSession).where(UserSession.user_id == user_id)
    if for_update:
        statement = statement.with_for_update()
    return list(db.scalars(statement).all())
