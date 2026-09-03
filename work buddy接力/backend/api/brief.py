"""
灾情简报 API 路由
对应愿景 5
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.database import get_db
from schemas.analytics import BriefGenerateRequest
from services.brief_generator import brief_generator, BRIEF_VERSIONS

router = APIRouter(prefix="/brief", tags=["灾情简报"])


@router.post("/generate", summary="生成灾情简报")
def generate_brief(
    req: BriefGenerateRequest,
    db: Session = Depends(get_db),
):
    """
    生成 AI 灾情简报（应急管理部通报风格）
    可指定版本（T+30min / T+1h / T+3h / T+6h ...）
    """
    result = brief_generator.generate(
        db,
        quake_time=datetime.fromisoformat(req.situation_data.get(
            "quake_time", "2025-03-28T14:20:52"
        )),
        version=req.version,
    )
    return result


@router.get("/versions", summary="获取简报版本列表")
def get_versions():
    """获取所有简报版本定义"""
    return BRIEF_VERSIONS


@router.get("/preview", summary="预览简报（不入库）")
def preview_brief(
    version: Optional[str] = None,
    quake_time: str = "2025-03-28T14:20:52",
    db: Session = Depends(get_db),
):
    """快速预览简报内容"""
    result = brief_generator.generate(
        db,
        quake_time=datetime.fromisoformat(quake_time),
        version=version,
    )
    return {
        "content": result["content"],
        "version": result["version"],
        "ai_powered": "注：本简报为社媒感知数据自动生成" not in result["content"],
        "generated_at": result["generated_at"],
    }
