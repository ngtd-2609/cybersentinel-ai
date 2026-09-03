from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cybersentinel_ai.db.models import AuditLog


def create_audit_log(
    db: Session,
    audit_log: AuditLog,
) -> AuditLog:
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def get_audit_logs(
    db: Session,
    *,
    limit: int,
    offset: int,
    action: str | None = None,
    target_type: str | None = None,
    user_id: int | None = None,
) -> tuple[list[AuditLog], int]:
    filters = []

    if action:
        filters.append(AuditLog.action == action.upper())

    if target_type:
        filters.append(AuditLog.target_type == target_type.upper())

    if user_id is not None:
        filters.append(AuditLog.user_id == user_id)

    items_statement = (
        select(AuditLog)
        .where(*filters)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(limit)
        .offset(offset)
    )
    count_statement = select(func.count(AuditLog.id)).where(*filters)

    items = list(db.scalars(items_statement).all())
    total = db.scalar(count_statement) or 0

    return items, total
