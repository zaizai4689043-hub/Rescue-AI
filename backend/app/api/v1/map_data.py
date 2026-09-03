from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.disaster import Disaster

router = APIRouter(tags=["地图数据"])


@router.get("/")
def get_map_data(
    bbox: Optional[str] = Query(None, description="范围过滤，格式: min_lat,min_lng,max_lat,max_lng"),
    db: Session = Depends(get_db),
):
    """轻量标记数据，仅用于地图标记"""
    query = db.query(
        Disaster.id,
        Disaster.title,
        Disaster.disaster_type,
        Disaster.severity,
        Disaster.status,
        Disaster.latitude,
        Disaster.longitude,
        Disaster.address,
    )
    if bbox:
        try:
            min_lat, min_lng, max_lat, max_lng = [float(x.strip()) for x in bbox.split(",")]
            query = query.filter(
                Disaster.latitude >= min_lat,
                Disaster.latitude <= max_lat,
                Disaster.longitude >= min_lng,
                Disaster.longitude <= max_lng,
            )
        except ValueError:
            pass
    rows = query.all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "disaster_type": r.disaster_type,
            "severity": r.severity,
            "status": r.status,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "address": r.address,
        }
        for r in rows
    ]


@router.get("/heatmap")
def get_heatmap(db: Session = Depends(get_db)):
    """按省份聚合灾情数量（简化：按 address 前缀聚合）"""
    from sqlalchemy import func

    # 由于地址不一定包含省份，这里用 address 字段做简单聚合
    # 若 address 为空则归入“未知区域”
    rows = (
        db.query(
            func.coalesce(func.substr(Disaster.address, 1, 3), "未知区域").label("name"),
            func.count(Disaster.id).label("value"),
        )
        .group_by("name")
        .all()
    )
    return [{"name": r.name, "value": r.value} for r in rows]
