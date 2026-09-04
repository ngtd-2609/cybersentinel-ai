from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from cybersentinel_ai.security import dependencies
from cybersentinel_ai.security.jwt import create_access_token


def test_get_current_user_rejects_inactive_user(monkeypatch):
    inactive_user = SimpleNamespace(
        id=1,
        email="disabled@cybersentinel.ai",
        is_active=False,
    )
    monkeypatch.setattr(
        dependencies,
        "get_user_by_email",
        lambda db, email: inactive_user,
    )

    token = create_access_token(inactive_user.email, "inactive-session")

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_current_user(token=token, db=object())

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Inactive user"


def test_get_current_user_allows_active_user(monkeypatch):
    active_user = SimpleNamespace(
        id=2,
        email="active@cybersentinel.ai",
        is_active=True,
    )
    monkeypatch.setattr(
        dependencies,
        "get_user_by_email",
        lambda db, email: active_user,
    )
    monkeypatch.setattr(
        dependencies,
        "is_user_session_active",
        lambda db, session_id, user_id: True,
    )

    token = create_access_token(active_user.email, "active-session")

    result = dependencies.get_current_user(
        token=token,
        db=object(),
    )

    assert result is active_user


def test_get_current_user_rejects_revoked_session(monkeypatch):
    active_user = SimpleNamespace(
        id=3,
        email="revoked@cybersentinel.ai",
        is_active=True,
    )
    monkeypatch.setattr(
        dependencies,
        "get_user_by_email",
        lambda db, email: active_user,
    )
    monkeypatch.setattr(
        dependencies,
        "is_user_session_active",
        lambda db, session_id, user_id: False,
    )

    token = create_access_token(active_user.email, "revoked-session")

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_current_user(token=token, db=object())

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Session revoked or expired"
