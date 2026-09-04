from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from cybersentinel_ai.auth.session_repository import (
    create_user_session,
    get_user_session,
    get_user_session_by_refresh_hash,
)
from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.models import User, UserSession
from cybersentinel_ai.security.jwt import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)


class InvalidRefreshTokenError(ValueError):
    pass


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_in: int


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def issue_user_session(
    db: Session,
    user: User,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> TokenPair:
    settings = get_settings()
    refresh_token = create_refresh_token()
    session = create_user_session(
        db,
        UserSession(
            user_id=user.id,
            refresh_token_hash=hash_refresh_token(refresh_token),
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.refresh_token_expire_days),
            ip_address=ip_address,
            user_agent=user_agent,
        ),
    )
    return TokenPair(
        access_token=create_access_token(user.email, session.id),
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        refresh_expires_in=settings.refresh_token_expire_days * 24 * 60 * 60,
    )


def rotate_user_session(
    db: Session,
    refresh_token: str,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[User, TokenPair]:
    now = datetime.now(UTC)
    current = get_user_session_by_refresh_hash(
        db,
        hash_refresh_token(refresh_token),
        for_update=True,
    )
    if (
        current is None
        or current.revoked_at is not None
        or _as_utc(current.expires_at) <= now
    ):
        raise InvalidRefreshTokenError("Invalid or expired refresh token")

    user = db.get(User, current.user_id)
    if user is None or not user.is_active:
        raise InvalidRefreshTokenError("Invalid or expired refresh token")

    replacement = issue_user_session(
        db,
        user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    replacement_session = get_user_session_by_refresh_hash(
        db,
        hash_refresh_token(replacement.refresh_token),
    )
    if replacement_session is None:
        raise RuntimeError("Replacement session was not persisted")

    current.revoked_at = now
    current.last_used_at = now
    current.replaced_by_id = replacement_session.id
    db.flush()
    return user, replacement


def revoke_user_session(
    db: Session,
    refresh_token: str,
    user_id: int,
) -> bool:
    session = get_user_session_by_refresh_hash(
        db,
        hash_refresh_token(refresh_token),
        for_update=True,
    )
    if session is None or session.user_id != user_id:
        return False
    if session.revoked_at is None:
        session.revoked_at = datetime.now(UTC)
        db.flush()
    return True


def is_user_session_active(
    db: Session,
    session_id: str,
    user_id: int,
) -> bool:
    session = get_user_session(db, session_id)
    return bool(
        session is not None
        and session.user_id == user_id
        and session.revoked_at is None
        and _as_utc(session.expires_at) > datetime.now(UTC)
    )
