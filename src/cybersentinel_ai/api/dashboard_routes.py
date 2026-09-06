from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import DashboardSummary
from cybersentinel_ai.db.dashboard_repository import get_dashboard_summary
from cybersentinel_ai.db.database import get_db
from cybersentinel_ai.security.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    database: DatabaseSession,
    current_user=Depends(get_current_user),
) -> DashboardSummary:
    return DashboardSummary.model_validate(
        get_dashboard_summary(database, user_id=current_user.id, role=current_user.role)
    )
