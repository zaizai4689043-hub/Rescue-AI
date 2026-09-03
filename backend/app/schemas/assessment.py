from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field


DamageLevelLiteral = Literal["minor", "moderate", "severe", "complete"]


class AssessmentCreate(BaseModel):
    disaster_id: int
    damage_level: DamageLevelLiteral = Field(..., description="minor/moderate/severe/complete")
    building_count_affected: Optional[int] = Field(0, ge=0)
    casualty_estimate: Optional[int] = Field(0, ge=0)
    injured_estimate: Optional[int] = Field(0, ge=0)
    area_affected: Optional[float] = Field(0.0, ge=0)
    infrastructure_damage: Optional[str] = None
    recommendations: Optional[str] = None


class AssessmentUpdate(BaseModel):
    damage_level: Optional[DamageLevelLiteral] = None
    building_count_affected: Optional[int] = Field(None, ge=0)
    casualty_estimate: Optional[int] = Field(None, ge=0)
    injured_estimate: Optional[int] = Field(None, ge=0)
    area_affected: Optional[float] = Field(None, ge=0)
    infrastructure_damage: Optional[str] = None
    recommendations: Optional[str] = None


class AssessorBrief(BaseModel):
    id: int
    username: str
    real_name: str

    model_config = {"from_attributes": True}


class DisasterBrief(BaseModel):
    id: int
    title: str
    disaster_type: str
    address: Optional[str] = None

    model_config = {"from_attributes": True}


class AssessmentResponse(BaseModel):
    id: int
    disaster_id: int
    assessor_id: int
    damage_level: str
    building_count_affected: int
    casualty_estimate: int
    injured_estimate: int
    area_affected: float
    infrastructure_damage: Optional[str] = None
    recommendations: Optional[str] = None
    disaster: Optional[DisasterBrief] = None
    assessor: Optional[AssessorBrief] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssessmentListResponse(BaseModel):
    items: List[AssessmentResponse]
    total: int
    page: int
    page_size: int
