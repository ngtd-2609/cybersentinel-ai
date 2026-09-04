from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from cybersentinel_ai.auth.session_repository import (
    create_user_session,
    get_user_session,
    get_user_session_by_refresh_hash,
    get_user_sessions,
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


class RefreshTokenReuseError(InvalidRefreshTokenError):
    def __init__(self, user_id: int):
        super().__init__("Invalid or expired refresh token")
        self.user_id = user_id


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
    if current is None or _as_utc(current.expires_at) <= now:
        raise InvalidRefreshTokenError("Invalid or expired refresh token")
    if current.revoked_at is not None:
        if current.replaced_by_id is not None:
            raise RefreshTokenReuseError(current.user_id)
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


def revoke_rotated_session_family(
    db: Session,
    refresh_token: str,
    user_id: int,
) -> bool:
    current = get_user_session_by_refresh_hash(
        db,
        hash_refresh_token(refresh_token),
        for_update=True,
    )
    if (
        current is None
        or current.user_id != user_id
        or current.replaced_by_id is None
    ):
        return False

    now = datetime.now(UTC)
    next_session_id = current.replaced_by_id
    visited = {current.id}
    while next_session_id is not None and next_session_id not in visited:
        visited.add(next_session_id)
        descendant = get_user_session(db, next_session_id, for_update=True)
        if descendant is None or descendant.user_id != user_id:
            break
        if descendant.revoked_at is None:
            descendant.revoked_at = now
            descendant.last_used_at = now
        next_session_id = descendant.replaced_by_id

    db.flush()
    return True


def revoke_all_user_sessions(db: Session, user_id: int) -> int:
    now = datetime.now(UTC)
    revoked = 0
    for session in get_user_sessions(db, user_id, for_update=True):
        if session.revoked_at is None:
            session.revoked_at = now
            session.last_used_at = now
            revoked += 1
    db.flush()
    return revoked


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
