from sqlalchemy import select
from sqlalchemy.orm import Session

from cybersentinel_ai.db.models import User


def get_all_users(
    db: Session,
) -> list[User]:
    return list(
        db.scalars(
            select(User)
        ).all()
    )


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    return db.scalar(
        select(User).where(
            User.id == user_id
        )
    )


def update_user_role(
    db: Session,
    user: User,
    role: str,
    *,
    commit: bool = True,
) -> User:
    user.role = role

    if commit:
        db.commit()
    else:
        db.flush()
    db.refresh(user)

    return user


def update_user_status(
    db: Session,
    user: User,
    is_active: bool,
    *,
    commit: bool = True,
) -> User:
    user.is_active = is_active

    if commit:
        db.commit()
    else:
        db.flush()
    db.refresh(user)

    return user
