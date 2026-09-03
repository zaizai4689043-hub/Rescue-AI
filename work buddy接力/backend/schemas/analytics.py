"""
分析相关 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class HotspotResponse(BaseModel):
    id: int
    location_name: str
    longitude: float
    latitude: float
    post_count: int
    urgency_score: float
    max_severity: int
    avg_severity: float
    damage_types: Optional[dict]
    sentiment_dist: Optional[dict]
    distress_count: int
    priority_level: Optional[str]
    priority_score: float
    priority_reason: Optional[str]
    has_rescue_team: bool
    rescue_status: str
    estimated_trapped: int
    road_accessible: bool
    hours_since_quake: float

    class Config:
        from_attributes = True


class PriorityRankingItem(BaseModel):
    hotspot_id: int
    location_name: str
    longitude: float
    latitude: float
    priority_level: str
    priority_score: float
    priority_reason: Optional[str]
    urgency_score: float
    post_count: int
    distress_count: int
    estimated_trapped: int
    has_rescue_team: bool
    road_accessible: bool
    factors: Optional[dict]


class DamageTypeDistribution(BaseModel):
    damage_type: str
    count: int
    percentage: float


class KeywordFrequency(BaseModel):
    keyword: str
    count: int
    trend: str  # rising/stable/falling


class SentimentTimelinePoint(BaseModel):
    timestamp: str
    urgent: int
    negative: int
    neutral: int
    hopeful: int
    total: int


class AnalyticsDashboard(BaseModel):
    summary: dict
    damage_type_distribution: List[DamageTypeDistribution]
    keyword_frequencies: List[KeywordFrequency]
    sentiment_timeline: List[SentimentTimelinePoint]
    top_distress_areas: List[dict]


class BriefResponse(BaseModel):
    id: int
    content: str
    generated_at: datetime
    situation_snapshot: Optional[dict]
    version: str  # T+30min, T+1h, etc.
    changes_from_previous: Optional[str]


class BriefGenerateRequest(BaseModel):
    situation_data: dict = Field(..., description="灾情态势数据")
    version: Optional[str] = None  # T+30min, T+1h etc.


class DecisionAnalyzeRequest(BaseModel):
    situation_data: dict = Field(..., description="当前灾情态势")
    epicenter: Optional[List[float]] = [95.94, 22.01]
    magnitude: Optional[float] = 7.7
    depth_km: Optional[float] = 10.0


class DecisionResult(BaseModel):
    priority_areas: List[dict]
    action_plan: str
    matched_cases: List[dict]
    risk_warnings: List[str]
    resource_suggestions: List[str]
    reference_case: Optional[str]


class CaseMatchResult(BaseModel):
    case_id: str
    name: str
    magnitude: float
    similarity_score: float
    match_dimensions: dict
    strategies: List[dict]
    lessons: List[str]
