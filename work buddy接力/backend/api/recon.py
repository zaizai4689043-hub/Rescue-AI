"""
空中侦察 API 路由
对应无人机空中救援模块 - 灾情侦察 / 路线研判
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.drone import ReconCreate, ReconImageUpload, ReconAnalyze
from services.recon_service import ReconService

router = APIRouter(prefix="/api/drone/recon", tags=["recon"])


@router.post("/create", summary="创建侦察任务")
def create_recon(data: ReconCreate, db: Session = Depends(get_db)):
    """创建空中侦察任务，自动分配有侦察能力的无人机"""
    result = ReconService.create_recon_mission(
        db, data.area_name, data.center_lng, data.center_lat,
        data.drone_id_str, data.hotspot_id
    )
    if not result:
        raise HTTPException(400, "无法创建侦察任务")
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/list", summary="侦察记录列表")
def get_recon_list(area_name: str = None, db: Session = Depends(get_db)):
    recons = ReconService.get_recon_list(db, area_name)
    return [_recon_to_dict(r) for r in recons]


@router.get("/{recon_id}", summary="获取侦察详情")
def get_recon(recon_id: int, db: Session = Depends(get_db)):
    from models.aerial_recon import AerialRecon
    recon = db.query(AerialRecon).filter(AerialRecon.id == recon_id).first()
    if not recon:
        raise HTTPException(404, "侦察记录不存在")
    return _recon_to_dict(recon)


@router.post("/{recon_id}/upload", summary="上传侦察图片")
def upload_image(recon_id: int, data: ReconImageUpload, db: Session = Depends(get_db)):
    recon = ReconService.upload_recon_image(db, recon_id, data.model_dump())
    if not recon:
        raise HTTPException(404, "侦察记录不存在")
    return _recon_to_dict(recon)


@router.post("/{recon_id}/analyze", summary="AI 路线分析")
def analyze_route(recon_id: int, data: ReconAnalyze, db: Session = Depends(get_db)):
    """
    AI 分析航拍画面，判断道路可通行性
    - 有图片：使用 Qwen-VL 视觉分析
    - 无图片：基于情报数据文本分析
    """
    recon = ReconService.analyze_route_with_ai(
        db, recon_id, data.image_b64, data.context_data
    )
    if not recon:
        raise HTTPException(404, "侦察记录不存在")
    return _recon_to_dict(recon)


@router.get("/routes/summary", summary="路线研判汇总")
def get_route_summary(db: Session = Depends(get_db)):
    """汇总所有侦察的路线研判结果"""
    return ReconService.get_route_summary(db)


def _recon_to_dict(r) -> dict:
    return {
        "id": r.id,
        "mission_id": r.mission_id,
        "drone_id_str": r.drone_id_str,
        "area_name": r.area_name,
        "center_lng": r.center_lng,
        "center_lat": r.center_lat,
        "coverage_sqkm": r.coverage_sqkm,
        "images": r.images or [],
        "videos": r.videos or [],
        "thermal_images": r.thermal_images or [],
        "lidar_point_count": r.lidar_point_count,
        "route_analysis": r.route_analysis,
        "route_assessment": r.route_assessment,
        "discovered_elements": r.discovered_elements or [],
        "survivor_signals": r.survivor_signals or [],
        "status": r.status,
        "analyzed_at": r.analyzed_at.isoformat() if r.analyzed_at else None,
        "analyzed_by": r.analyzed_by,
    }
