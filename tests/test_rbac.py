from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from cybersentinel_ai.auth import admin_service
from cybersentinel_ai.security.rbac import UserRole, require_role


@pytest.mark.parametrize(
    "role",
    ["ADMIN", "SENIOR_ANALYST", "ANALYST"],
)
def test_incident_writer_roles_are_allowed(role):
    user = SimpleNamespace(role=role)
    checker = require_role(
        UserRole.ADMIN,
        UserRole.SENIOR_ANALYST,
        UserRole.ANALYST,
    )

    assert checker(current_user=user) is user


def test_viewer_is_denied_write_access():
    checker = require_role(
        UserRole.ADMIN,
        UserRole.SENIOR_ANALYST,
        UserRole.ANALYST,
    )

    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=SimpleNamespace(role="VIEWER"))

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions"


def test_admin_can_assign_senior_analyst_role(monkeypatch):
    user = SimpleNamespace(id=7, role="ANALYST")
    monkeypatch.setattr(
        admin_service,
        "get_user_by_id",
        lambda db, user_id: user,
    )
    monkeypatch.setattr(
        admin_service,
        "update_user_role",
        lambda db, target, role: SimpleNamespace(
            id=target.id,
            role=role,
        ),
    )

    updated = admin_service.change_user_role(
        db=object(),
        user_id=user.id,
        role="SENIOR_ANALYST",
    )

    assert updated.role == "SENIOR_ANALYST"
