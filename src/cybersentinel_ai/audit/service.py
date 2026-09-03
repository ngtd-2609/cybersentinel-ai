from sqlalchemy.orm import Session

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
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        description=description,
    )

    return create_audit_log(
        db,
        audit_log,
    )


def list_audit_logs(
    db: Session,
) -> list[AuditLog]:
    return get_audit_logs(db)
