"""社情入库与检索服务：消费统一事件（UnifiedSocialEvent），按 raw_ref 去重落库。

供 api/v1/social.py 与离线回填脚本 app/scripts/seed_social.py 共用，
回填脚本直接调用本模块函数入库，不经过 HTTP。
"""
from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.social_post import SocialPost
from app.services.social.adapters import UnifiedSocialEvent


def ingest_event(db: Session, event: UnifiedSocialEvent) -> Tuple[SocialPost, bool]:
    """单条入库；返回 (记录, 是否新插入)。重复（raw_ref 已存在）直接返回已有记录"""
    existing = db.query(SocialPost).filter(SocialPost.raw_ref == event.raw_ref).first()
    if existing:
        return existing, False
    geo = event.geo
    post = SocialPost(
        platform=event.platform,
        post_id=event.event_id.split("-", 1)[1] if "-" in event.event_id else None,
        raw_ref=event.raw_ref,
        text=event.text,
        ts=event.ts,
        latitude=geo.latitude if geo else None,
        longitude=geo.longitude if geo else None,
        geo_name=geo.name if geo else None,
        signal_type=event.signal_type.value,
        confidence=event.confidence,
        urgency_hint=event.urgency_hint,
        tags=event.tags or None,
        offset_min=event.offset_min,
        sentiment=event.sentiment,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post, True


def batch_ingest(db: Session, events: List[UnifiedSocialEvent]) -> dict:
    """批量入库（逐条去重）；返回统计摘要"""
    inserted, skipped = 0, 0
    for ev in events:
        if not ev.text or not ev.text.strip():
            skipped += 1
            continue
        _, created = ingest_event(db, ev)
        inserted += 1 if created else 0
        skipped += 0 if created else 1
    return {
        "received": len(events),
        "inserted": inserted,
        "skipped_duplicates": skipped,
        "total": db.query(func.count(SocialPost.id)).scalar(),
    }


def get_posts(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    platform: Optional[str] = None,
    signal_type: Optional[str] = None,
    urgency_hint: Optional[str] = None,
    min_confidence: Optional[float] = None,
    keyword: Optional[str] = None,
) -> Tuple[List[SocialPost], int]:
    """分页 + 过滤检索"""
    q = db.query(SocialPost)
    if platform:
        q = q.filter(SocialPost.platform == platform)
    if signal_type:
        q = q.filter(SocialPost.signal_type == signal_type)
    if urgency_hint:
        q = q.filter(SocialPost.urgency_hint == urgency_hint)
    if min_confidence is not None:
        q = q.filter(SocialPost.confidence >= min_confidence)
    if keyword:
        q = q.filter(SocialPost.text.like(f"%{keyword}%"))
    total = q.count()
    items = (
        q.order_by(SocialPost.ts.desc().nulls_last(), SocialPost.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def get_heatmap(db: Session, grid: float = 0.5, platform: Optional[str] = None) -> List[List[float]]:
    """按 geo 网格聚合输出 [[lng, lat, score], ...]：
    格子中心坐标 + 聚合得分（帖子数 × 平均可信度，可信度缺失按 0.5 计）。
    无坐标帖不参与聚合。"""
    q = db.query(SocialPost).filter(SocialPost.latitude.is_not(None), SocialPost.longitude.is_not(None))
    if platform:
        q = q.filter(SocialPost.platform == platform)
    buckets = {}
    for p in q.all():
        gx, gy = round(p.longitude / grid), round(p.latitude / grid)
        conf = p.confidence if p.confidence is not None else 0.5
        cnt, total_conf = buckets.get((gx, gy), (0, 0.0))
        buckets[(gx, gy)] = (cnt + 1, total_conf + conf)
    points = []
    for (gx, gy), (cnt, total_conf) in buckets.items():
        points.append([round(gx * grid, 4), round(gy * grid, 4), round(cnt * (total_conf / cnt), 3)])
    points.sort(key=lambda x: x[2], reverse=True)
    return points
