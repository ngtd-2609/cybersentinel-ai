from sqlalchemy import select
from sqlalchemy.orm import Session

from cybersentinel_ai.db.models import User


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    return db.scalar(
        select(User).where(
            User.email == email
        )
    )


def create_user(
    db: Session,
    user: User,
) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)

    return user
