from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel, Field


class ResourceCreate(BaseModel):
    name: str = Field(..., max_length=200)
    resource_type: str = Field(..., description="material/equipment/personnel/vehicle")
    quantity: int = Field(..., ge=0)
    unit: str = Field(..., max_length=50)
    location: str = Field(..., max_length=300)
    description: Optional[str] = None


class ResourceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    resource_type: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=300)
    status: Optional[str] = None
    description: Optional[str] = None


class ResourceResponse(BaseModel):
    id: int
    name: str
    resource_type: str
    quantity: int
    unit: str
    location: str
    status: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResourceListResponse(BaseModel):
    items: List[ResourceResponse]
    total: int
    page: int
    page_size: int


class ResourceDispatch(BaseModel):
    target_location: str = Field(..., max_length=300)
    quantity: Optional[int] = Field(None, ge=1)


class ResourceStatistics(BaseModel):
    total_count: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
