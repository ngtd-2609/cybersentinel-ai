from sqlalchemy import select
from sqlalchemy.orm import Session

from cybersentinel_ai.db.models import User


def get_user_by_email(
    db: Session,
    email: str,
    *,
    for_update: bool = False,
) -> User | None:
    statement = select(User).where(User.email == email)
    if for_update:
        statement = statement.with_for_update()
    return db.scalar(statement)


def get_user_by_username(
    db: Session,
    username: str,
) -> User | None:
    return db.scalar(
        select(User).where(
            User.username == username
        )
    )


def create_user(
    db: Session,
    user: User,
    *,
    commit: bool = True,
) -> User:
    db.add(user)
    if commit:
        db.commit()
    else:
        db.flush()
    db.refresh(user)

    return user
