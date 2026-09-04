from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.auth.admin_schemas import (
    UpdateRoleRequest,
    UserAdminResponse,
)
from cybersentinel_ai.auth.admin_service import (
    change_user_role,
    list_users,
)
from cybersentinel_ai.db.database import atomic, get_db
from cybersentinel_ai.security.rbac import (
    UserRole,
    require_role,
)

router = APIRouter(
    prefix="/admin/users",
    tags=["admin-users"],
)


@router.get(
    "",
    response_model=list[UserAdminResponse],
)
def get_users(
    db: Session = Depends(get_db),
    _=Depends(
        require_role(UserRole.ADMIN)
    ),
):
    return list_users(db)


@router.patch(
    "/{user_id}/role",
    response_model=UserAdminResponse,
)
def update_role(
    user_id: int,
    payload: UpdateRoleRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(UserRole.ADMIN)
    ),
):
    try:
        with atomic(db):
            user = change_user_role(
                db,
                user_id,
                payload.role,
                commit=False,
            )

            log_action(
                db,
                current_user.id,
                "UPDATE_ROLE",
                f"Changed user {user.email} role to {payload.role}",
                "USER",
                user.id,
                commit=False,
            )

        return user
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
