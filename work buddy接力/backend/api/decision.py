"""
AI 决策助手 API 路由
对应愿景 6
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from schemas.analytics import DecisionAnalyzeRequest
from services.decision_assistant import decision_assistant
from services.case_matcher import case_matcher

router = APIRouter(prefix="/decision", tags=["AI决策助手"])


@router.post("/analyze", summary="AI 决策分析")
def analyze(
    req: DecisionAnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    AI 决策分析：预测最需要优先救援的地区 + 案例匹配 + 行动方案
    """
    result = decision_assistant.analyze(
        db,
        epicenter=tuple(req.epicenter) if req.epicenter else (95.94, 22.01),
        magnitude=req.magnitude or 7.7,
        depth_km=req.depth_km or 10.0,
    )
    return result


@router.get("/cases", summary="案例知识库列表")
def get_cases(db: Session = Depends(get_db)):
    """获取所有救援案例"""
    from models.rescue_case import RescueCase
    cases = db.query(RescueCase).all()
    if not cases:
        # 从 JSON 加载
        json_cases = case_matcher.load_cases_from_json()
        return {"items": json_cases, "source": "json", "count": len(json_cases)}
    return {
        "items": [{
            "case_id": c.case_id,
            "name": c.name,
            "magnitude": c.magnitude,
            "casualties": c.casualties,
            "location": c.location,
            "occurred_at": str(c.occurred_at) if c.occurred_at else None,
            "tags": c.tags,
            "terrain": c.terrain,
        } for c in cases],
        "source": "database",
        "count": len(cases)
    }


@router.get("/cases/{case_id}", summary="案例详情")
def get_case_detail(case_id: str, db: Session = Depends(get_db)):
    """获取单个案例的详细信息"""
    from models.rescue_case import RescueCase
    case = db.query(RescueCase).filter(RescueCase.case_id == case_id).first()

    if not case:
        # 从 JSON 查找
        json_cases = case_matcher.load_cases_from_json()
        case_data = next((c for c in json_cases if c.get("case_id") == case_id), None)
        if not case_data:
            raise HTTPException(status_code=404, detail="案例不存在")
        return case_data

    return {
        "case_id": case.case_id,
        "name": case.name,
        "magnitude": case.magnitude,
        "depth_km": case.depth_km,
        "location": case.location,
        "latitude": case.latitude,
        "longitude": case.longitude,
        "occurred_at": str(case.occurred_at) if case.occurred_at else None,
        "casualties": case.casualties,
        "affected_population": case.affected_population,
        "terrain": case.terrain,
        "building_type": case.building_type,
        "population_density": case.population_density,
        "season": case.season,
        "weather": case.weather,
        "infrastructure": case.infrastructure,
        "secondary_hazard": case.secondary_hazard,
        "warning_capability": case.warning_capability,
        "occurrence_time": case.occurrence_time,
        "timeline": case.timeline,
        "strategies": case.strategies,
        "lessons": case.lessons,
        "tags": case.tags,
    }


@router.post("/cases/sync", summary="同步案例到数据库")
def sync_cases(db: Session = Depends(get_db)):
    """将 JSON 案例知识库同步到数据库"""
    count = case_matcher.sync_to_database(db)
    return {"synced": count}


@router.post("/match", summary="案例匹配")
def match_cases(
    magnitude: float = 7.7,
    depth_km: float = 10.0,
    terrain: Optional[str] = None,
    building_type: Optional[str] = None,
    season: Optional[str] = None,
    top_n: int = Query(3, ge=1, le=8),
    db: Session = Depends(get_db),
):
    """手动匹配历史案例"""
    query = {
        "magnitude": magnitude,
        "depth_km": depth_km,
        "terrain": terrain or "山区",
        "building_type": building_type or "砖混",
        "population_density": "中",
        "season": season or "春",
        "infrastructure": "一般",
        "secondary_hazard": "",
        "warning_capability": "有",
        "occurrence_time": "午间",
    }
    results = case_matcher.match(db, query, top_n)
    return {"query": query, "matched": results}
