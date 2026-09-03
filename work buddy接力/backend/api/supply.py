"""
物资投送 API 路由
对应无人机空中救援模块 - 物资运输
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.drone import DeliveryRequest, DeliveryConfirm, DeliveryPlan
from services.supply_service import SupplyService

router = APIRouter(prefix="/api/drone/supply", tags=["supply"])


@router.post("/request", summary="创建物资投送需求")
def create_delivery(data: DeliveryRequest, db: Session = Depends(get_db)):
    """根据灾情热点优先级自动生成物资投送需求"""
    delivery = SupplyService.create_delivery_request(db, data.hotspot_id, data.custom_manifest)
    if not delivery:
        raise HTTPException(404, "灾情热点不存在")
    return _delivery_to_dict(delivery)


@router.post("/plan", summary="规划投送航线")
def plan_delivery(data: DeliveryPlan, db: Session = Depends(get_db)):
    """规划投送航线并分配无人机"""
    result = SupplyService.plan_delivery_route(db, data.delivery_id, data.drone_id_str)
    if not result:
        raise HTTPException(404, "投送记录不存在")
    if "error" in result:
        raise HTTPException(400, result["message"])
    return result


@router.get("/queue", summary="获取投送队列")
def get_queue(db: Session = Depends(get_db)):
    deliveries = SupplyService.get_delivery_queue(db)
    return [_delivery_to_dict(d) for d in deliveries]


@router.get("/stats", summary="投送统计")
def get_stats(db: Session = Depends(get_db)):
    return SupplyService.get_delivery_stats(db)


@router.get("/packages", summary="标准物资包列表")
def get_packages():
    """返回各优先级对应的标准物资包"""
    from services.supply_service import STANDARD_PACKAGES
    return {k: v for k, v in STANDARD_PACKAGES.items()}


@router.post("/{delivery_id}/confirm", summary="确认物资收到")
def confirm_delivery(delivery_id: int, data: DeliveryConfirm, db: Session = Depends(get_db)):
    delivery = SupplyService.confirm_delivery(
        db, delivery_id, data.received_count, data.received_by, data.note
    )
    if not delivery:
        raise HTTPException(404, "投送记录不存在")
    return _delivery_to_dict(delivery)


@router.post("/ai-plan", summary="AI 辅助物资清单规划")
def ai_plan(hotspot_data: dict, available_drones: list, db: Session = Depends(get_db)):
    """AI 根据灾情热点推荐最优物资投送方案"""
    result = SupplyService.ai_plan_supplies(hotspot_data, available_drones)
    if not result:
        return {"error": "AI 服务不可用", "fallback": "请使用标准物资包"}
    return result


def _delivery_to_dict(d) -> dict:
    return {
        "id": d.id,
        "mission_id": d.mission_id,
        "drone_id_str": d.drone_id_str,
        "target_location": d.target_location,
        "target_lng": d.target_lng,
        "target_lat": d.target_lat,
        "manifest": d.manifest,
        "total_weight_kg": d.total_weight_kg,
        "total_items": d.total_items,
        "category_summary": d.category_summary,
        "status": d.status,
        "priority": d.priority,
        "drop_method": d.drop_method,
        "drop_altitude_m": d.drop_altitude_m,
        "requested_at": d.requested_at.isoformat() if d.requested_at else None,
        "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
        "confirmed_at": d.confirmed_at.isoformat() if d.confirmed_at else None,
        "received_by": d.received_by,
        "received_count": d.received_count,
        "shortage_count": d.shortage_count,
    }
