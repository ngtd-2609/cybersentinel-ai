from sqlalchemy.orm import Session

from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.auth.repository import (
    create_user,
    get_user_by_email,
    get_user_by_username,
)
from cybersentinel_ai.auth.schemas import UserCreate
from cybersentinel_ai.db.database import atomic
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

    existing_username = get_user_by_username(
        db,
        payload.username,
    )

    if existing_username:
        raise ValueError("Username already exists")

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(
            payload.password
        ),
        full_name=payload.full_name,
    )

    with atomic(db):
        created_user = create_user(
            db,
            user,
            commit=False,
        )

        log_action(
            db,
            created_user.id,
            "CREATE_USER",
            f"Created user {created_user.email}",
            "USER",
            created_user.id,
            commit=False,
        )

    return created_user


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

    if not user.is_active:
        log_action(
            db,
            user.id,
            "LOGIN_BLOCKED",
            f"Disabled user {user.email} attempted login",
            "USER",
            user.id,
        )
        return None

    return user
