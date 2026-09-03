from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    real_name: str = Field(..., max_length=50)
    phone: str = Field(..., max_length=20)
    role: Optional[str] = Field(None, description="admin/commander/rescuer/medic")
    organization: Optional[str] = Field(None, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    real_name: str
    phone: str
    role: str
    organization: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
