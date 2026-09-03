from pydantic import BaseModel, ConfigDict


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
