"""
无人机 API 路由
对应无人机空中救援模块：机队管理 / 遥测 / 任务 / 巡逻仿真
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.drone import (
    DroneOut, DroneRegister, TelemetryFrame, FleetStatus,
    MissionAssign, MissionOut, MissionComplete,
    PatrolSimCreate, PatrolSimStep,
)
from services.drone_service import DroneService

router = APIRouter(prefix="/api/drone", tags=["drone"])


# ---- 机队管理 ----

@router.get("/fleet", response_model=list, summary="获取机队列表")
def get_fleet(db: Session = Depends(get_db)):
    drones = DroneService.get_fleet(db)
    return [_drone_to_dict(d) for d in drones]


@router.get("/fleet/status", response_model=FleetStatus, summary="机队状态汇总")
def get_fleet_status(db: Session = Depends(get_db)):
    return DroneService.get_fleet_status_summary(db)


@router.post("/fleet/register", response_model=dict, summary="注册无人机")
def register_drone(data: DroneRegister, db: Session = Depends(get_db)):
    drone = DroneService.register_drone(db, data.model_dump())
    return _drone_to_dict(drone)


@router.post("/fleet/init-sim", summary="初始化仿真机队")
def init_sim_fleet(db: Session = Depends(get_db)):
    """初始化 3 台仿真无人机（演示用）"""
    DroneService.init_sim_fleet(db)
    return {"message": "仿真机队已初始化", "fleet": [d.drone_id_str for d in DroneService.get_fleet(db)]}


# ---- 遥测 ----

@router.post("/telemetry", summary="接收遥测帧（仿真/真机统一入口）")
def receive_telemetry(frame: TelemetryFrame, db: Session = Depends(get_db)):
    """
    对应演示版 applyTelemetry() + POST /drone/telemetry
    真机可经大疆 Cloud API / MAVLink 转发为本格式
    """
    drone = DroneService.apply_telemetry(db, frame.model_dump())
    if not drone:
        raise HTTPException(404, f"无人机 {frame.id} 不存在")
    return {"status": "ok", "drone_id": drone.drone_id_str, "battery": drone.battery}


@router.get("/telemetry/{drone_id_str}", summary="获取遥测数据")
def get_telemetry(drone_id_str: str, db: Session = Depends(get_db)):
    data = DroneService.get_telemetry(db, drone_id_str)
    if not data:
        raise HTTPException(404, "无人机不存在")
    return data


# ---- 任务 ----

@router.post("/mission/assign", summary="分配任务")
def assign_mission(data: MissionAssign, drone_id_str: str, db: Session = Depends(get_db)):
    mission = DroneService.assign_mission(db, drone_id_str, data.model_dump())
    if not mission:
        raise HTTPException(400, "无人机不存在或当前忙")
    return {"mission_id": mission.id, "status": mission.status}


@router.get("/missions", summary="获取进行中的任务")
def get_active_missions(db: Session = Depends(get_db)):
    missions = DroneService.get_active_missions(db)
    return [_mission_to_dict(m) for m in missions]


@router.post("/mission/{mission_id}/complete", summary="完成任务")
def complete_mission(mission_id: int, result: MissionComplete = None, db: Session = Depends(get_db)):
    mission = DroneService.complete_mission(db, mission_id, result.model_dump() if result else None)
    if not mission:
        raise HTTPException(404, "任务不存在")
    return {"mission_id": mission.id, "status": mission.status}


@router.post("/mission/{mission_id}/abort", summary="中止任务")
def abort_mission(mission_id: int, reason: str = "", db: Session = Depends(get_db)):
    mission = DroneService.abort_mission(db, mission_id, reason)
    if not mission:
        raise HTTPException(404, "任务不存在")
    return {"mission_id": mission.id, "status": mission.status, "reason": reason}


# ---- 巡逻仿真（保留演示版动画逻辑） ----

@router.post("/patrol/create", summary="创建巡逻仿真会话")
def create_patrol_sim(data: PatrolSimCreate):
    """
    创建巡逻仿真会话，返回初始状态
    前端可据此驱动画布动画（蛇形扫描 / 激光点云 / 热成像探测）
    """
    sim = DroneService.create_patrol_simulation(
        drone_id_str=data.drone_id_str,
        canvas_width=data.canvas_width,
        canvas_height=data.canvas_height,
        row_count=data.row_count,
    )
    return sim


@router.post("/patrol/start", summary="启动巡逻")
def start_patrol(sim: dict):
    """启动巡逻搜索（对应演示版 btnScan.onclick）"""
    return DroneService.start_patrol(sim)


@router.post("/patrol/stop", summary="停止巡逻")
def stop_patrol(sim: dict):
    return DroneService.stop_patrol(sim)


@router.post("/patrol/step", summary="推进仿真一帧")
def step_patrol(data: PatrolSimStep):
    """
    推进巡逻仿真一帧
    返回更新后的 sim 和本帧事件列表
    """
    sim, events = DroneService.step_patrol_simulation(data.sim, data.dt, data.survivors)
    return {"sim": sim, "events": events}


# ---- 工具函数 ----

def _drone_to_dict(d) -> dict:
    return {
        "id": d.id,
        "drone_id_str": d.drone_id_str,
        "call_sign": d.call_sign,
        "model": d.model,
        "capabilities": d.capabilities or [],
        "max_payload_kg": d.max_payload_kg,
        "max_flight_min": d.max_flight_min,
        "max_speed_ms": d.max_speed_ms,
        "status": d.status,
        "battery": d.battery,
        "longitude": d.longitude,
        "latitude": d.latitude,
        "altitude_m": d.altitude_m,
        "speed_ms": d.speed_ms,
        "heading": d.heading,
        "current_mission_id": d.current_mission_id,
        "home_base": d.home_base,
        "payload_type": d.payload_type,
        "payload_detail": d.payload_detail,
        "is_simulated": d.is_simulated,
        "last_telemetry_at": d.last_telemetry_at.isoformat() if d.last_telemetry_at else None,
    }


def _mission_to_dict(m) -> dict:
    return {
        "id": m.id,
        "mission_type": m.mission_type,
        "drone_id": m.drone_id,
        "target_location": m.target_location,
        "target_lng": m.target_lng,
        "target_lat": m.target_lat,
        "description": m.description,
        "status": m.status,
        "delivery_status": m.delivery_status,
        "cargo_weight_kg": m.cargo_weight_kg,
        "waypoints": m.waypoints,
        "planned_distance_m": m.planned_distance_m,
        "assigned_at": m.assigned_at.isoformat() if m.assigned_at else None,
        "started_at": m.started_at.isoformat() if m.started_at else None,
        "completed_at": m.completed_at.isoformat() if m.completed_at else None,
    }
