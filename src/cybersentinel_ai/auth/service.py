from datetime import UTC, datetime, timedelta
from math import ceil

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.auth.repository import (
    create_user,
    get_user_by_email,
    get_user_by_username,
)
from cybersentinel_ai.auth.schemas import UserCreate
from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.database import atomic
from cybersentinel_ai.db.models import User
from cybersentinel_ai.security.jwt import (
    hash_password,
    verify_password,
)


class AccountLockedError(ValueError):
    def __init__(self, retry_after: int):
        super().__init__("Account temporarily locked")
        self.retry_after = retry_after


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


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
    now = datetime.now(UTC)
    settings = get_settings()
    authenticated_user: User | None = None
    lock_error: AccountLockedError | None = None

    with atomic(db):
        user = get_user_by_email(db, email, for_update=True)

        if user is None:
            log_action(
                db,
                None,
                "LOGIN_FAILED",
                f"Failed login attempt for {email}",
                "USER",
                None,
                commit=False,
            )
        elif user.locked_until is not None and _as_utc(user.locked_until) > now:
            retry_after = max(1, ceil((_as_utc(user.locked_until) - now).total_seconds()))
            log_action(
                db,
                user.id,
                "LOGIN_BLOCKED",
                f"Locked user {user.email} attempted login",
                "USER",
                user.id,
                commit=False,
            )
            lock_error = AccountLockedError(retry_after)
        elif not user.is_active:
            log_action(
                db,
                user.id,
                "LOGIN_BLOCKED",
                f"Disabled user {user.email} attempted login",
                "USER",
                user.id,
                commit=False,
            )
        elif not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            user.last_failed_login_at = now
            action = "LOGIN_FAILED"
            description = f"Failed login attempt for {user.email}"

            if user.failed_login_attempts >= settings.account_lockout_attempts:
                user.locked_until = now + timedelta(minutes=settings.account_lockout_minutes)
                action = "ACCOUNT_LOCKED"
                description = (
                    f"Locked user {user.email} after "
                    f"{user.failed_login_attempts} failed login attempts"
                )
                lock_error = AccountLockedError(settings.account_lockout_minutes * 60)

            log_action(
                db,
                user.id,
                action,
                description,
                "USER",
                user.id,
                commit=False,
            )
        else:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_failed_login_at = None
            db.flush()
            authenticated_user = user

    if lock_error is not None:
        raise lock_error
    return authenticated_user


def bootstrap_first_admin(db: Session, payload: UserCreate) -> User:
    with atomic(db):
        bind = db.get_bind()
        if bind.dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(493827156)"))

        existing_admin = db.scalar(
            select(User.id).where(User.role == "ADMIN").limit(1)
        )
        if existing_admin is not None:
            raise ValueError("An administrator already exists")
        if get_user_by_email(db, payload.email) is not None:
            raise ValueError("Email already exists")
        if get_user_by_username(db, payload.username) is not None:
            raise ValueError("Username already exists")

        admin = create_user(
            db,
            User(
                email=payload.email,
                username=payload.username,
                hashed_password=hash_password(payload.password),
                full_name=payload.full_name,
                role="ADMIN",
            ),
            commit=False,
        )
        log_action(
            db,
            admin.id,
            "BOOTSTRAP_ADMIN",
            f"Bootstrapped first administrator {admin.email}",
            "USER",
            admin.id,
            commit=False,
        )
    return admin
