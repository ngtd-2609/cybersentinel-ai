from sqlalchemy import select
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
) -> list[AuditLog]:
    return list(
        db.scalars(
            select(AuditLog).order_by(
                AuditLog.created_at.desc()
            )
        ).all()
    )
