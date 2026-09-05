from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import AlertRuleCreate, AlertRuleRead, AlertRuleUpdate
from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.db.database import atomic, get_db
from cybersentinel_ai.db.models import AlertRule
from cybersentinel_ai.security.rbac import UserRole, require_role

router = APIRouter(prefix="/alert-rules", tags=["Alert Rules"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def _apply_payload(rule: AlertRule, values: dict) -> None:
    for key, value in values.items():
        if key in {"severities", "notification_channels"}:
            value = ",".join(value)
        setattr(rule, key, value)


@router.get(
    "",
    response_model=list[AlertRuleRead],
    dependencies=[Depends(require_role(*tuple(UserRole)))],
)
def list_rules(database: DatabaseSession) -> list[AlertRule]:
    return list(
        database.scalars(
            select(AlertRule).order_by(AlertRule.priority.asc(), AlertRule.id.asc())
        ).all()
    )


@router.post("", response_model=AlertRuleRead, status_code=201)
def create_rule(
    payload: AlertRuleCreate,
    database: DatabaseSession,
    current_user=Depends(require_role(UserRole.ADMIN)),
) -> AlertRule:
    with atomic(database):
        rule = AlertRule()
        _apply_payload(rule, payload.model_dump())
        database.add(rule)
        database.flush()
        log_action(
            database,
            current_user.id,
            "CREATE_ALERT_RULE",
            f"Created alert rule {rule.name}",
            "ALERT_RULE",
            rule.id,
            commit=False,
        )
    database.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=AlertRuleRead)
def update_rule(
    rule_id: int,
    payload: AlertRuleUpdate,
    database: DatabaseSession,
    current_user=Depends(require_role(UserRole.ADMIN)),
) -> AlertRule:
    with atomic(database):
        rule = database.get(AlertRule, rule_id)
        if rule is None:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        _apply_payload(rule, payload.model_dump(exclude_unset=True))
        log_action(
            database,
            current_user.id,
            "UPDATE_ALERT_RULE",
            f"Updated alert rule {rule.name}",
            "ALERT_RULE",
            rule.id,
            commit=False,
        )
    database.refresh(rule)
    return rule
