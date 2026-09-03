from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.disaster import Disaster
from app.services.ai_service import analyze_building_damage

router = APIRouter(tags=["AI分析"])


class AnalyzeRequest(BaseModel):
    disaster_id: Optional[int] = None
    image_url: Optional[str] = None


@router.post("/analyze")
def trigger_analysis(
    req: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """触发AI建筑损毁分析，结果保存到 Disaster.ai_analysis_result"""
    result = analyze_building_damage(image_url=req.image_url)
    if req.disaster_id:
        disaster = db.query(Disaster).filter(Disaster.id == req.disaster_id).first()
        if not disaster:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="灾情不存在")
        disaster.ai_analysis_result = result
        db.commit()
        db.refresh(disaster)
    return result


@router.get("/{disaster_id}")
def get_analysis(disaster_id: int, db: Session = Depends(get_db)):
    """获取某灾情的AI分析结果"""
    disaster = db.query(Disaster).filter(Disaster.id == disaster_id).first()
    if not disaster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="灾情不存在")
    if not disaster.ai_analysis_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="暂无AI分析结果")
    return disaster.ai_analysis_result
