from typing import Literal

from pydantic import BaseModel, ConfigDict

from cybersentinel_ai.auth.schemas import UserCreate


class AdminUserCreate(UserCreate):
    role: Literal["ADMIN", "SENIOR_ANALYST", "ANALYST", "VIEWER"] = "VIEWER"


class UserAdminResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str | None
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UpdateRoleRequest(BaseModel):
    role: str
