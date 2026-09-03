from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.models.user import User
from app.dependencies import get_current_active_user
from app.services.ai_assistant_service import get_reply
from app.services.ai_advisory_service import generate_advisory

router = APIRouter(tags=["AI助手"])


class ChatRequest(BaseModel):
    message: str


class AdvisoryRequest(BaseModel):
    """参谋研判入参：字段对齐 SocialPostResponse"""
    text: str
    signal_type: str = "unknown"
    geo_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    confidence: Optional[float] = None
    urgency_hint: Optional[str] = None
    sentiment: Optional[str] = None


@router.post("/chat")
def chat(req: ChatRequest):
    """AI救援助手聊天接口（Qwen优先，预设兜底，永不500）"""
    return get_reply(req.message)


@router.post("/advisory")
def advisory(
    req: AdvisoryRequest,
    current_user: User = Depends(get_current_active_user),
):
    """参谋研判：针对单条社情帖生成双方案 + 三维可信度拆解。

    需要 JWT（与平台其余写/算操作一致）。返回 {plans, credibility, provider}。
    """
    return generate_advisory(
        text=req.text,
        signal_type=req.signal_type,
        geo_name=req.geo_name,
        latitude=req.latitude,
        longitude=req.longitude,
        confidence=req.confidence,
        urgency_hint=req.urgency_hint,
        sentiment=req.sentiment,
    )
