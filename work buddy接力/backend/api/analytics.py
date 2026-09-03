"""
分析仪表盘 API 路由
对应愿景 4
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["分析仪表盘"])


@router.get("/dashboard", summary="多维分析仪表盘")
def get_dashboard(db: Session = Depends(get_db)):
    """获取完整的多维分析仪表盘数据"""
    return analytics_service.get_dashboard(db)


@router.get("/damage-types", summary="损毁类型分布")
def get_damage_types(db: Session = Depends(get_db)):
    """获取损毁类型分布（饼图）"""
    return analytics_service.get_damage_type_distribution(db)


@router.get("/keywords", summary="关键词频率排行")
def get_keywords(
    top_n: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """获取关键词频率排行（柱状图）"""
    return analytics_service.get_keyword_frequencies(db, top_n)


@router.get("/sentiment-timeline", summary="情感时间线")
def get_sentiment_timeline(
    interval_minutes: int = Query(30, ge=5, le=240),
    db: Session = Depends(get_db),
):
    """获取时间线情感变化（折线图）"""
    return analytics_service.get_sentiment_timeline(db, interval_minutes)


@router.get("/emerging-keywords", summary="新兴关键词检测")
def get_emerging_keywords(
    threshold: int = Query(5, ge=1),
    db: Session = Depends(get_db),
):
    """检测近期突然大量出现的关键词（次生灾害预警）"""
    return analytics_service.detect_emerging_keywords(db, threshold)


@router.get("/distress-areas", summary="呼救区域排行")
def get_distress_areas(
    top_n: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """获取呼救信号最多的区域"""
    return analytics_service.get_top_distress_areas(db, top_n)
