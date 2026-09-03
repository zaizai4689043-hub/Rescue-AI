from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel, Field


class VolunteerCreate(BaseModel):
    user_id: int
    name: str = Field(..., max_length=100)
    phone: str = Field(..., max_length=20)
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[int] = Field(0, ge=0)
    current_location: Optional[str] = Field(None, max_length=300)


class VolunteerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None
    current_location: Optional[str] = Field(None, max_length=300)
    notes: Optional[str] = None


class UserBrief(BaseModel):
    id: int
    username: str
    real_name: str
    phone: str

    model_config = {"from_attributes": True}


class VolunteerResponse(BaseModel):
    id: int
    user_id: int
    name: str
    phone: str
    skills: Optional[List[str]] = None
    experience_years: int
    status: str
    current_location: Optional[str] = None
    notes: Optional[str] = None
    user: Optional[UserBrief] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VolunteerListResponse(BaseModel):
    items: List[VolunteerResponse]
    total: int
    page: int
    page_size: int


class VolunteerAssign(BaseModel):
    task_description: str = Field(..., max_length=500)
    location: str = Field(..., max_length=300)


class VolunteerStatistics(BaseModel):
    total_count: int
    by_status: Dict[str, int]
    by_skill: Dict[str, int]
