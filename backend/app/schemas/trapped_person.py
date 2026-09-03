from datetime import datetime
from typing import Optional, List, Dict, Literal

from pydantic import BaseModel, Field


TrappedStatusLiteral = Literal["waiting", "searching", "rescued", "transferred"]
TrappedPriorityLiteral = Literal["red", "yellow", "green", "black"]


class TrappedPersonCreate(BaseModel):
    disaster_id: int
    name: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=200)
    gender: Optional[Literal["male", "female", "unknown"]] = None
    location: str = Field(..., max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    priority: Optional[TrappedPriorityLiteral] = "red"
    condition: Optional[str] = None
    reported_by: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class TrappedPersonUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=200)
    gender: Optional[Literal["male", "female", "unknown"]] = None
    location: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    status: Optional[TrappedStatusLiteral] = None
    priority: Optional[TrappedPriorityLiteral] = None
    condition: Optional[str] = None
    reported_by: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class TrappedPersonResponse(BaseModel):
    id: int
    disaster_id: int
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str
    priority: str
    condition: Optional[str] = None
    reported_by: Optional[str] = None
    reported_at: datetime
    rescued_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TrappedPersonListResponse(BaseModel):
    items: List[TrappedPersonResponse]
    total: int
    page: int
    page_size: int


class TrappedPersonStatistics(BaseModel):
    total: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    rescue_rate: float
