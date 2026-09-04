from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from cybersentinel_ai.auth.router import router
from cybersentinel_ai.auth.schemas import UserCreate
from cybersentinel_ai.auth.service import (
    AccountLockedError,
    authenticate_user,
    bootstrap_first_admin,
)
from cybersentinel_ai.core.config import Settings, get_settings
from cybersentinel_ai.db.database import Base, build_engine, get_db
from cybersentinel_ai.db.models import AuditLog, User
from cybersentinel_ai.security.jwt import hash_password, verify_password


@pytest.fixture
def database_factory(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'identity-hardening.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    yield factory
    engine.dispose()


def test_public_registration_is_disabled_by_default(database_factory):
    def override_get_db() -> Generator[Session, None, None]:
        with database_factory() as database:
            yield database

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.post(
        "/auth/register",
        json={
            "email": "viewer@example.test",
            "username": "viewer",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Public registration is disabled"}


def test_public_registration_can_be_explicitly_enabled(database_factory):
    def override_get_db() -> Generator[Session, None, None]:
        with database_factory() as database:
            yield database

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None,
        public_registration_enabled=True,
    )
    client = TestClient(app)

    response = client.post(
        "/auth/register",
        json={
            "email": "viewer@example.test",
            "username": "viewer",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["role"] == "VIEWER"


def test_locked_account_response_includes_retry_after(monkeypatch):
    def locked(*_args, **_kwargs):
        raise AccountLockedError(42)

    monkeypatch.setattr("cybersentinel_ai.auth.router.authenticate_user", locked)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: object()
    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={"email": "locked@example.test", "password": "any-password"},
    )

    assert response.status_code == 429
    assert response.headers["retry-after"] == "42"
    assert response.json() == {"detail": "Account temporarily locked"}


def test_first_admin_bootstrap_is_one_time_and_audited(database_factory):
    payload = UserCreate(
        email="admin@example.test",
        username="first-admin",
        password="StrongPassword123!",
        full_name="First Admin",
    )

    with database_factory() as database:
        admin = bootstrap_first_admin(database, payload)
        audit = database.scalar(
            select(AuditLog).where(AuditLog.action == "BOOTSTRAP_ADMIN")
        )

        assert admin.role == "ADMIN"
        assert verify_password(payload.password, admin.hashed_password)
        assert audit is not None
        assert audit.user_id == admin.id

        with pytest.raises(ValueError, match="administrator already exists"):
            bootstrap_first_admin(
                database,
                UserCreate(
                    email="other-admin@example.test",
                    username="other-admin",
                    password="AnotherStrong123!",
                ),
            )

        assert len(database.scalars(select(User)).all()) == 1


def test_failed_logins_lock_account_and_success_resets_state(
    database_factory,
    monkeypatch,
):
    monkeypatch.setattr(
        "cybersentinel_ai.auth.service.get_settings",
        lambda: Settings(
            _env_file=None,
            account_lockout_attempts=3,
            account_lockout_minutes=10,
        ),
    )
    with database_factory() as database:
        user = User(
            email="analyst@example.test",
            username="analyst",
            hashed_password=hash_password("StrongPassword123!"),
            role="ANALYST",
        )
        database.add(user)
        database.commit()

        assert authenticate_user(database, user.email, "wrong-1") is None
        assert authenticate_user(database, user.email, "wrong-2") is None
        with pytest.raises(AccountLockedError) as locked:
            authenticate_user(database, user.email, "wrong-3")

        database.refresh(user)
        assert locked.value.retry_after == 600
        assert user.failed_login_attempts == 3
        assert user.locked_until is not None
        actions = database.scalars(
            select(AuditLog.action).order_by(AuditLog.id)
        ).all()
        assert actions == ["LOGIN_FAILED", "LOGIN_FAILED", "ACCOUNT_LOCKED"]

        with pytest.raises(AccountLockedError):
            authenticate_user(database, user.email, "StrongPassword123!")

        user.locked_until = datetime.now(UTC) - timedelta(seconds=1)
        database.commit()
        assert authenticate_user(
            database,
            user.email,
            "StrongPassword123!",
        ) is not None
        database.refresh(user)
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
        assert user.last_failed_login_at is None
