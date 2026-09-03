from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from cybersentinel_ai.security import dependencies
from cybersentinel_ai.security.jwt import create_access_token


def test_get_current_user_rejects_inactive_user(monkeypatch):
    inactive_user = SimpleNamespace(
        email="disabled@cybersentinel.ai",
        is_active=False,
    )
    monkeypatch.setattr(
        dependencies,
        "get_user_by_email",
        lambda db, email: inactive_user,
    )

    token = create_access_token(inactive_user.email)

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_current_user(token=token, db=object())

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Inactive user"


def test_get_current_user_allows_active_user(monkeypatch):
    active_user = SimpleNamespace(
        email="active@cybersentinel.ai",
        is_active=True,
    )
    monkeypatch.setattr(
        dependencies,
        "get_user_by_email",
        lambda db, email: active_user,
    )

    token = create_access_token(active_user.email)

    result = dependencies.get_current_user(
        token=token,
        db=object(),
    )

    assert result is active_user
