from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.social_post import SocialPost
from app.schemas.social import (
    BatchIngestResult,
    SocialBatchIngest,
    SocialHeatmapResponse,
    SocialPostIngest,
    SocialPostListResponse,
    SocialPostResponse,
    ingest_to_event,
)
from app.services.social import service as social_service
from app.services.social.adapters import SIGNAL_TYPE_LABELS, SignalType

router = APIRouter(tags=["社情平台"])


def _to_response(post: SocialPost) -> SocialPostResponse:
    resp = SocialPostResponse.model_validate(post)
    try:
        resp.signal_type_label = SIGNAL_TYPE_LABELS.get(SignalType(post.signal_type))
    except ValueError:
        resp.signal_type_label = None
    return resp


@router.post("/ingest", response_model=SocialPostResponse, status_code=status.HTTP_201_CREATED)
def ingest(payload: SocialPostIngest, db: Session = Depends(get_db)):
    """单条社情帖入库（统一事件口径；raw_ref 重复时幂等返回已有记录）"""
    post, created = social_service.ingest_event(db, ingest_to_event(payload))
    return _to_response(post)


@router.post("/batch-ingest", response_model=BatchIngestResult)
def batch_ingest(payload: SocialBatchIngest, db: Session = Depends(get_db)):
    """批量入库（离线回填同款逻辑，逐条哈希去重）"""
    events = [ingest_to_event(p) for p in payload.posts]
    return social_service.batch_ingest(db, events)


@router.get("/posts", response_model=SocialPostListResponse)
def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    platform: Optional[str] = None,
    signal_type: Optional[str] = None,
    urgency_hint: Optional[str] = None,
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """分页检索社情帖（支持平台/信号类型/紧急度/最低可信度/正文关键词过滤）"""
    items, total = social_service.get_posts(
        db, page=page, page_size=page_size,
        platform=platform, signal_type=signal_type, urgency_hint=urgency_hint,
        min_confidence=min_confidence, keyword=keyword,
    )
    return SocialPostListResponse(
        items=[_to_response(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/heatmap", response_model=SocialHeatmapResponse)
def heatmap(
    grid: float = Query(0.5, gt=0.01, le=10, description="网格边长（经纬度）"),
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """社情热力：按 geo 网格聚合输出 [[lng, lat, score], ...]"""
    points = social_service.get_heatmap(db, grid=grid, platform=platform)
    return SocialHeatmapResponse(grid=grid, count=len(points), points=points)
