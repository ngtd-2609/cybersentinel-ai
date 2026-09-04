from sqlalchemy.orm import Session

from cybersentinel_ai.auth.admin_repository import (
    get_all_users,
    get_user_by_id,
    update_user_role,
    update_user_status,
)
from cybersentinel_ai.db.models import User


def list_users(
    db: Session,
) -> list[User]:
    return get_all_users(db)


def change_user_role(
    db: Session,
    user_id: int,
    role: str,
    *,
    commit: bool = True,
) -> User:
    user = get_user_by_id(
        db,
        user_id,
    )

    if not user:
        raise ValueError(
            "User not found"
        )

    allowed_roles = {
        "ADMIN",
        "SENIOR_ANALYST",
        "ANALYST",
        "VIEWER",
    }

    if role not in allowed_roles:
        raise ValueError(
            "Invalid role"
        )

    if commit:
        return update_user_role(db, user, role)

    return update_user_role(db, user, role, commit=False)


def change_user_status(
    db: Session,
    user_id: int,
    is_active: bool,
    *,
    commit: bool = True,
) -> User:
    user = get_user_by_id(
        db,
        user_id,
    )

    if not user:
        raise ValueError(
            "User not found"
        )

    if commit:
        return update_user_status(db, user, is_active)

    return update_user_status(db, user, is_active, commit=False)
