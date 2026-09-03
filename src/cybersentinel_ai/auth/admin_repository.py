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
) -> User:
    user.role = role

    db.commit()
    db.refresh(user)

    return user


def update_user_status(
    db: Session,
    user: User,
    is_active: bool,
) -> User:
    user.is_active = is_active

    db.commit()
    db.refresh(user)

    return user
