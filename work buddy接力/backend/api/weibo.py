"""
微博数据 API 路由
对应愿景 2
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from models.weibo_post import WeiboPost
from schemas.weibo import (
    WeiboPostCreate, WeiboPostBatchCreate, WeiboPostResponse,
    FunnelStats, IngestResult, BatchIngestResult
)
from services.weibo_pipeline import weibo_pipeline

router = APIRouter(prefix="/weibo", tags=["微博数据"])


@router.post("/ingest", response_model=IngestResult, summary="导入单条微博")
def ingest_post(
    post: WeiboPostCreate,
    db: Session = Depends(get_db),
):
    """手动导入单条微博数据，自动执行清洗→过滤→NLP→入库"""
    result = weibo_pipeline.ingest_post(
        db,
        raw_text=post.raw_text or post.text,
        published_at=post.published_at,
        user_verified=post.user_verified,
        offset_min=post.offset_min,
    )
    return result


@router.post("/batch-ingest", response_model=BatchIngestResult, summary="批量导入微博")
def batch_ingest(
    data: WeiboPostBatchCreate,
    db: Session = Depends(get_db),
):
    """批量导入微博数据"""
    epicenter = tuple(data.epicenter) if data.epicenter else (95.94, 22.01)
    posts = [
        {
            "text": p.text,
            "raw_text": p.raw_text or p.text,
            "published_at": p.published_at,
            "user_verified": p.user_verified,
            "offset_min": p.offset_min,
        }
        for p in data.posts
    ]
    result = weibo_pipeline.batch_ingest(db, posts, epicenter)
    return result


@router.get("/posts", summary="查询微博列表")
def get_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sentiment: Optional[str] = None,
    damage_type: Optional[str] = None,
    distress_only: bool = False,
    include_filtered: bool = False,
    db: Session = Depends(get_db),
):
    """分页查询微博列表，支持筛选"""
    query = db.query(WeiboPost)

    if not include_filtered:
        query = query.filter(WeiboPost.is_filtered == False)

    if sentiment:
        query = query.filter(WeiboPost.sentiment == sentiment)
    if damage_type:
        query = query.filter(WeiboPost.damage_type == damage_type)
    if distress_only:
        query = query.filter(WeiboPost.has_distress_signal == True)

    total = query.count()
    posts = query.order_by(WeiboPost.published_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [WeiboPostResponse.model_validate(p).model_dump() for p in posts],
    }


@router.get("/funnel", response_model=FunnelStats, summary="数据漏斗统计")
def get_funnel(db: Session = Depends(get_db)):
    """获取微博数据漏斗统计"""
    return weibo_pipeline.get_funnel_stats(db)


@router.post("/rebuild-hotspots", summary="重建灾情热点")
def rebuild_hotspots(db: Session = Depends(get_db)):
    """从微博数据重建灾情热点"""
    from services.hotspot_service import hotspot_service
    count = hotspot_service.rebuild_hotspots(db)
    return {"hotspots_created": count}


@router.post("/refresh-priority", summary="刷新优先级")
def refresh_priority(
    generate_reasons: bool = True,
    db: Session = Depends(get_db),
):
    """刷新所有热点的优先级排序"""
    from services.priority_engine import priority_engine
    count = priority_engine.refresh_all(db, generate_reasons)
    return {"updated": count}
