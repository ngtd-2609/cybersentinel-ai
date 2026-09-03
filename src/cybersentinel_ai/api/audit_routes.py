from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from cybersentinel_ai.audit.schemas import AuditLogResponse
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
    response_model=list[AuditLogResponse],
)
def get_audit_logs(
    db: Session = Depends(get_db),
    _=Depends(
        require_role(UserRole.ADMIN)
    ),
):
    return list_audit_logs(db)
