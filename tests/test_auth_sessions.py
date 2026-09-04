from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from cybersentinel_ai.auth.session_repository import (
    get_user_session_by_refresh_hash,
)
from cybersentinel_ai.auth.session_service import (
    InvalidRefreshTokenError,
    RefreshTokenReuseError,
    is_user_session_active,
    issue_user_session,
    revoke_rotated_session_family,
    revoke_user_session,
    rotate_user_session,
)
from cybersentinel_ai.db.database import Base, atomic, build_engine
from cybersentinel_ai.db.models import User
from cybersentinel_ai.security.jwt import decode_access_token, hash_refresh_token


def build_session() -> tuple[Session, User]:
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    database = Session(engine)
    user = User(
        email="session@example.test",
        username="session-user",
        hashed_password="not-used",
        role="ANALYST",
        is_active=True,
    )
    database.add(user)
    database.commit()
    return database, user


def test_refresh_rotation_revokes_old_token_and_logout_revokes_access():
    database, user = build_session()
    with database:
        with atomic(database):
            first = issue_user_session(database, user)

        first_claims = decode_access_token(first.access_token)
        assert first_claims["sub"] == user.email
        assert first_claims["type"] == "access"
        assert first_claims["jti"]
        assert is_user_session_active(database, first_claims["sid"], user.id)

        with atomic(database):
            rotated_user, second = rotate_user_session(
                database,
                first.refresh_token,
            )

        assert rotated_user.id == user.id
        assert second.refresh_token != first.refresh_token
        assert not is_user_session_active(database, first_claims["sid"], user.id)

        second_claims = decode_access_token(second.access_token)
        with atomic(database):
            _, third = rotate_user_session(database, second.refresh_token)
        third_claims = decode_access_token(third.access_token)

        with pytest.raises(RefreshTokenReuseError) as reused, atomic(database):
            rotate_user_session(database, first.refresh_token)

        assert reused.value.user_id == user.id
        with atomic(database):
            assert revoke_rotated_session_family(
                database,
                first.refresh_token,
                user.id,
            )

        assert not is_user_session_active(database, second_claims["sid"], user.id)
        assert not is_user_session_active(database, third_claims["sid"], user.id)

        with atomic(database):
            fourth = issue_user_session(database, user)
        fourth_claims = decode_access_token(fourth.access_token)
        with atomic(database):
            assert revoke_user_session(database, fourth.refresh_token, user.id)

        assert not is_user_session_active(database, fourth_claims["sid"], user.id)


def test_expired_refresh_token_cannot_rotate():
    database, user = build_session()
    with database:
        with atomic(database):
            tokens = issue_user_session(database, user)

        stored = get_user_session_by_refresh_hash(
            database,
            hash_refresh_token(tokens.refresh_token),
        )
        assert stored is not None
        stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        database.commit()

        with pytest.raises(InvalidRefreshTokenError), atomic(database):
            rotate_user_session(database, tokens.refresh_token)
