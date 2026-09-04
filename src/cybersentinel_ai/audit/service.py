from sqlalchemy.orm import Session

from cybersentinel_ai.audit.context import get_request_context
from cybersentinel_ai.audit.repository import (
    create_audit_log,
    get_audit_logs,
)
from cybersentinel_ai.db.models import AuditLog


def log_action(
    db: Session,
    user_id: int | None,
    action: str,
    description: str,
    target_type: str | None = None,
    target_id: int | None = None,
    *,
    commit: bool = True,
) -> AuditLog:
    request_context = get_request_context()
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        description=description,
        request_id=request_context.request_id if request_context else None,
        ip_address=request_context.ip_address if request_context else None,
        user_agent=request_context.user_agent if request_context else None,
    )

    return create_audit_log(
        db,
        audit_log,
        commit=commit,
    )


def list_audit_logs(
    db: Session,
    *,
    limit: int,
    offset: int,
    action: str | None = None,
    target_type: str | None = None,
    user_id: int | None = None,
) -> tuple[list[AuditLog], int]:
    return get_audit_logs(
        db,
        limit=limit,
        offset=offset,
        action=action,
        target_type=target_type,
        user_id=user_id,
    )
