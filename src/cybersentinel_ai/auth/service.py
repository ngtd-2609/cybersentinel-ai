from sqlalchemy.orm import Session

from cybersentinel_ai.auth.repository import (
    create_user,
    get_user_by_email,
)
from cybersentinel_ai.auth.schemas import UserCreate
from cybersentinel_ai.db.models import User
from cybersentinel_ai.security.jwt import (
    hash_password,
    verify_password,
)


def register_user(
    db: Session,
    payload: UserCreate,
) -> User:
    existing = get_user_by_email(
        db,
        payload.email,
    )

    if existing:
        raise ValueError("Email already exists")

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(
            payload.password
        ),
        full_name=payload.full_name,
    )

    return create_user(
        db,
        user,
    )


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    user = get_user_by_email(
        db,
        email,
    )

    if not user:
        return None

    if not verify_password(
        password,
        user.hashed_password,
    ):
        return None

    return user
