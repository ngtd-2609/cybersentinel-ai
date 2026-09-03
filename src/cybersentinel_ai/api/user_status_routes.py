from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.auth.admin_schemas import UserAdminResponse
from cybersentinel_ai.auth.admin_service import change_user_status
from cybersentinel_ai.auth.admin_status_schemas import (
    UpdateStatusRequest,
)
from cybersentinel_ai.db.database import get_db
from cybersentinel_ai.security.rbac import (
    UserRole,
    require_role,
)

router = APIRouter(
    prefix="/admin/users",
    tags=["admin-users"],
)


@router.patch(
    "/{user_id}/status",
    response_model=UserAdminResponse,
)
def update_status(
    user_id: int,
    payload: UpdateStatusRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(UserRole.ADMIN)
    ),
):
    try:
        user = change_user_status(
            db,
            user_id,
            payload.is_active,
        )

        log_action(
            db,
            current_user.id,
            "UPDATE_STATUS",
            f"Changed user {user.email} active status to {payload.is_active}",
            "USER",
            user.id,
        )

        return user

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
