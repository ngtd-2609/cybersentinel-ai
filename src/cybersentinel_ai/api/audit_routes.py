from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from cybersentinel_ai.audit.schemas import AuditLogPage
from cybersentinel_ai.audit.service import list_audit_logs
from cybersentinel_ai.db.database import get_db
from cybersentinel_ai.security.rbac import (
    UserRole,
    require_role,
)

router = APIRouter(
    prefix="/admin/audit-logs",
    tags=["audit"],
)


@router.get(
    "",
    response_model=AuditLogPage,
)
def get_audit_logs(
    db: Session = Depends(get_db),
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    action: str | None = None,
    target_type: str | None = None,
    user_id: Annotated[int | None, Query(ge=1)] = None,
    _=Depends(
        require_role(UserRole.ADMIN)
    ),
) -> AuditLogPage:
    items, total = list_audit_logs(
        db,
        limit=limit,
        offset=offset,
        action=action,
        target_type=target_type,
        user_id=user_id,
    )

    return AuditLogPage(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
