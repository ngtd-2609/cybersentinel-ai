import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from cybersentinel_ai.api import main
from cybersentinel_ai.core.config import Settings
from cybersentinel_ai.db.database import get_db

client = TestClient(main.app)


def test_security_headers_are_added():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["permissions-policy"]


def test_readiness_checks_database():
    class Database:
        def execute(self, statement):
            return statement

    main.app.dependency_overrides[get_db] = lambda: Database()
    try:
        response = client.get("/ready")
    finally:
        main.app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_readiness_reports_database_failure():
    class Database:
        def execute(self, statement):
            raise SQLAlchemyError("unavailable")

    main.app.dependency_overrides[get_db] = lambda: Database()
    try:
        response = client.get("/ready")
    finally:
        main.app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503


def test_login_rate_limit(monkeypatch):
    monkeypatch.setattr(main.settings, "login_rate_limit_attempts", 2)
    monkeypatch.setattr(
        "cybersentinel_ai.auth.router.authenticate_user",
        lambda db, email, password: None,
    )
    monkeypatch.setattr(
        "cybersentinel_ai.auth.router.log_action",
        lambda *args, **kwargs: None,
    )
    main.app.dependency_overrides[get_db] = lambda: object()
    main.login_failures.clear()

    try:
        first = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "wrong"},
        )
        second = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "wrong"},
        )
        limited = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "wrong"},
        )
    finally:
        main.login_failures.clear()
        main.app.dependency_overrides.pop(get_db, None)

    assert first.status_code == 401
    assert second.status_code == 401
    assert limited.status_code == 429
    assert int(limited.headers["retry-after"]) >= 1
    assert limited.headers["x-request-id"]


def test_production_rejects_weak_jwt_secret():
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(
            _env_file=None,
            environment="production",
            enforce_production_config=True,
            secret_key="too-short",
        )


def test_production_accepts_strong_jwt_secret():
    settings = Settings(
        _env_file=None,
        environment="production",
        enforce_production_config=True,
        secret_key="a-unique-production-secret-with-32-chars",
        redis_url="redis://redis:6379/0",
    )

    assert settings.environment == "production"


def test_request_id_header_is_preserved_and_invalid_value_is_replaced():
    supplied = client.get("/health", headers={"X-Request-ID": "trace-test-123"})
    invalid = client.get("/health", headers={"X-Request-ID": "invalid request id"})

    assert supplied.headers["x-request-id"] == "trace-test-123"
    assert invalid.headers["x-request-id"] != "invalid request id"
    assert len(invalid.headers["x-request-id"]) == 36
