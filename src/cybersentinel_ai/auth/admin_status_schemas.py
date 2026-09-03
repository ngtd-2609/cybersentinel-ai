from pydantic import BaseModel


class UpdateStatusRequest(BaseModel):
    is_active: bool
