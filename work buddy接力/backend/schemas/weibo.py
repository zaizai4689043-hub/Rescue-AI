"""
微博相关 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class WeiboPostBase(BaseModel):
    text: str
    published_at: datetime
    offset_min: Optional[float] = None
    user_verified: bool = False


class WeiboPostCreate(WeiboPostBase):
    raw_text: Optional[str] = None


class WeiboPostBatchCreate(BaseModel):
    posts: List[WeiboPostCreate]
    epicenter: Optional[List[float]] = [95.94, 22.01]  # [lng, lat]


class WeiboPostResponse(BaseModel):
    id: int
    post_id: str
    text: str
    published_at: datetime
    offset_min: Optional[float]
    ner_locations: Optional[List[Any]]
    sentiment: Optional[str]
    damage_type: Optional[str]
    keywords: Optional[List[Any]]
    severity_vote: int
    credibility: float
    has_distress_signal: bool
    distress_keywords: Optional[List[Any]]
    user_verified: bool
    is_filtered: bool
    filter_reason: Optional[str]
    source: str

    class Config:
        from_attributes = True


class FunnelStats(BaseModel):
    total: int
    filtered: int
    active: int
    by_damage_type: dict
    by_sentiment: dict
    distress_signals: int


class IngestResult(BaseModel):
    status: str
    post_id: str
    filter_reason: Optional[str] = None
    nlp: Optional[dict] = None


class BatchIngestResult(BaseModel):
    ingested: int
    filtered: int
    exists: int
    no_keyword: int
    errors: int
