from datetime import datetime
from typing import Optional, List, Any, Dict, Literal

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse
from app.models.disaster import DisasterType

DISASTER_TYPES = [e.value for e in DisasterType]

DisasterTypeLiteral = Literal["earthquake", "aftershock", "building_collapse", "road_damage", "landslide", "secondary_hazard"]


class DisasterCreate(BaseModel):
    title: str = Field(..., max_length=200)
    disaster_type: DisasterTypeLiteral = Field(
        ..., description="Disaster type: earthquake/aftershock/building_collapse/road_damage/landslide/secondary_hazard"
    )
    severity: int = Field(..., ge=1, le=5)
    disaster_level: Optional[Literal["特别重大", "重大", "较大", "一般"]] = None
    estimated_people_trapped: Optional[int] = Field(None, ge=0)
    estimated_economic_loss: Optional[float] = Field(None, ge=0)
    description: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = Field(None, max_length=500)
    image_urls: Optional[List[str]] = None


class DisasterUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    disaster_type: Optional[DisasterTypeLiteral] = None
    severity: Optional[int] = Field(None, ge=1, le=5)
    disaster_level: Optional[Literal["特别重大", "重大", "较大", "一般"]] = None
    estimated_people_trapped: Optional[int] = Field(None, ge=0)
    estimated_economic_loss: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = Field(None, max_length=500)
    image_urls: Optional[List[str]] = None
    ai_analysis_result: Optional[Dict[str, Any]] = None


# 看板状态迁移矩阵（新情报→待批准→已派遣→核验→闭环；驳回=confirmed→reported）
ALLOWED_TRANSITIONS = {
    "reported": {"confirmed"},
    "confirmed": {"dispatched", "reported"},
    "dispatched": {"verify"},
    "verify": {"resolved"},
    # 旧 4 值数据的兼容路径（processing 可走向任一终态）
    "processing": {"dispatched", "verify", "resolved"},
    "resolved": set(),
}


class DisasterStatusUpdate(BaseModel):
    status: str = Field(..., description="目标状态：reported/confirmed/dispatched/verify/resolved")


class ReporterBrief(BaseModel):
    id: int
    username: str
    real_name: str
    phone: str

    model_config = {"from_attributes": True}


class DisasterResponse(BaseModel):
    id: int
    title: str
    disaster_type: str
    severity: int
    disaster_level: Optional[str] = None
    estimated_people_trapped: Optional[int] = None
    estimated_economic_loss: Optional[float] = None
    description: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    status: str
    reporter_id: int
    reporter: Optional[ReporterBrief] = None
    image_urls: Optional[List[str]] = None
    ai_analysis_result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DisasterListResponse(BaseModel):
    items: List[DisasterResponse]
    total: int
    page: int
    page_size: int


class TrendItem(BaseModel):
    date: str
    count: int


class DisasterStatistics(BaseModel):
    total_count: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    recent_trend: List[TrendItem]
