from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    target_type: str | None
    target_id: int | None
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
