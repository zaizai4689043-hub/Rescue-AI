from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.services.social.adapters import (
    GeoPoint,
    SignalType,
    UnifiedSocialEvent,
    derive_urgency,
    make_raw_ref,
    normalize_signal_type,
)

SIGNAL_TYPES = [e.value for e in SignalType]


class SocialPostIngest(BaseModel):
    """单条社情帖入库载荷（ingest / batch-ingest 共用）"""
    platform: str = Field("weibo", max_length=20, description="来源平台：weibo/douyin/xiaohongshu")
    post_id: Optional[str] = Field(None, max_length=64, description="平台内原帖 id，缺失时按正文哈希去重")
    text: str = Field(..., min_length=1, description="已做隐私剥离的正文")
    ts: Optional[datetime] = Field(None, description="发布时间（北京时间口径）")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    geo_name: Optional[str] = Field(None, max_length=200)
    signal_type: Optional[str] = Field(None, description="中文标签或英文枚举值，无法识别落 unknown")
    confidence: Optional[float] = Field(None, ge=0, le=1)
    urgency_hint: Optional[str] = Field(None, pattern="^(high|medium|low)$", description="缺省时按信号类型/评分派生")
    tags: Optional[List[str]] = None
    offset_min: Optional[int] = Field(None, ge=0, description="震后分钟偏移（回放口径）")
    sentiment: Optional[str] = Field(None, max_length=20)
    severity_vote: Optional[int] = Field(None, ge=1, le=5, description="上游严重度评分，仅用于派生紧急度")


class SocialBatchIngest(BaseModel):
    posts: List[SocialPostIngest] = Field(..., min_length=1)


class SocialPostResponse(BaseModel):
    id: int
    platform: str
    post_id: Optional[str] = None
    raw_ref: str
    text: str
    ts: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geo_name: Optional[str] = None
    signal_type: str
    signal_type_label: Optional[str] = None
    confidence: Optional[float] = None
    urgency_hint: Optional[str] = None
    tags: Optional[List[str]] = None
    offset_min: Optional[int] = None
    sentiment: Optional[str] = None
    ingested_at: datetime

    model_config = {"from_attributes": True}


class SocialPostListResponse(BaseModel):
    items: List[SocialPostResponse]
    total: int
    page: int
    page_size: int


class SocialHeatmapResponse(BaseModel):
    grid: float
    count: int
    points: List[List[float]] = Field(description="[[lng, lat, score], ...] 按 score 降序")


class BatchIngestResult(BaseModel):
    received: int
    inserted: int
    skipped_duplicates: int
    total: int


def ingest_to_event(payload: SocialPostIngest) -> UnifiedSocialEvent:
    """API 载荷 → 统一事件：补 raw_ref、归一信号类型、派生紧急度"""
    signal = normalize_signal_type(payload.signal_type)
    geo = None
    if payload.latitude is not None and payload.longitude is not None:
        geo = GeoPoint(latitude=payload.latitude, longitude=payload.longitude, name=payload.geo_name)
    raw_ref = make_raw_ref(payload.platform, payload.post_id, payload.text)
    event_id = f"{payload.platform}-{payload.post_id}" if payload.post_id else f"{payload.platform}-{raw_ref[:12]}"
    return UnifiedSocialEvent(
        event_id=event_id,
        platform=payload.platform,
        raw_ref=raw_ref,
        text=payload.text.strip(),
        ts=payload.ts,
        geo=geo,
        signal_type=signal,
        confidence=payload.confidence,
        urgency_hint=payload.urgency_hint or derive_urgency(signal, payload.severity_vote),
        tags=payload.tags or [],
        offset_min=payload.offset_min,
        sentiment=payload.sentiment,
    )
