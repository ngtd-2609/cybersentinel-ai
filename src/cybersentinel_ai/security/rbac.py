from enum import Enum

from fastapi import Depends, HTTPException

from cybersentinel_ai.security.dependencies import get_current_user


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    SENIOR_ANALYST = "SENIOR_ANALYST"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


def require_role(
    *roles: UserRole,
):
    def checker(
        current_user=Depends(get_current_user),
    ):
        if current_user.role not in [
            role.value for role in roles
        ]:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
            )

        return current_user

    return checker
