"""
无人机模块 Schemas
对应无人机空中救援模块的请求/响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ---- 无人机 ----
class DroneOut(BaseModel):
    id: int
    drone_id_str: str
    call_sign: Optional[str] = ""
    model: Optional[str] = ""
    capabilities: Optional[List[str]] = []
    max_payload_kg: Optional[float] = 0
    max_flight_min: Optional[float] = 30
    max_speed_ms: Optional[float] = 15
    status: str = "standby"
    battery: float = 100
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    altitude_m: Optional[float] = 0
    speed_ms: Optional[float] = 0
    heading: Optional[float] = 0
    current_mission_id: Optional[int] = None
    home_base: Optional[str] = ""
    payload_type: Optional[str] = "none"
    payload_detail: Optional[Any] = None
    is_simulated: bool = True
    last_telemetry_at: Optional[str] = None

    class Config:
        from_attributes = True


class DroneRegister(BaseModel):
    drone_id_str: str
    call_sign: Optional[str] = ""
    model: Optional[str] = ""
    capabilities: Optional[List[str]] = ["search"]
    max_payload_kg: Optional[float] = 0
    max_flight_min: Optional[float] = 30
    max_speed_ms: Optional[float] = 15
    home_base: Optional[str] = ""
    home_lng: Optional[float] = None
    home_lat: Optional[float] = None
    is_simulated: Optional[bool] = True


class TelemetryFrame(BaseModel):
    """遥测帧（与 DRONE_TELEMETRY_SCHEMA 兼容）"""
    id: str = Field(..., description="无人机编号")
    x: Optional[float] = Field(None, description="地图坐标 x / 经度")
    y: Optional[float] = Field(None, description="地图坐标 y / 纬度")
    heading: Optional[float] = Field(None, description="航向")
    battery: Optional[float] = Field(None, description="电量 0-100")
    mode: Optional[str] = Field(None, description="飞行模式")
    payload: Optional[Any] = Field(None, description="载荷数据")


class FleetStatus(BaseModel):
    total: int
    standby: int
    searching: int
    supplying: int
    recon: int
    returning: int
    charging: int
    offline: int
    avg_battery: float


# ---- 任务 ----
class MissionAssign(BaseModel):
    mission_type: str = Field("search", description="search/supply/recon/comm_relay")
    target_location: Optional[str] = ""
    target_lng: Optional[float] = None
    target_lat: Optional[float] = None
    description: Optional[str] = ""
    cargo_manifest: Optional[List[Any]] = None
    cargo_weight_kg: Optional[float] = 0
    waypoints: Optional[List[Any]] = []
    planned_distance_m: Optional[float] = 0
    disaster_id: Optional[int] = None
    hotspot_id: Optional[int] = None


class MissionOut(BaseModel):
    id: int
    mission_type: str
    drone_id: Optional[int] = None
    target_location: Optional[str] = ""
    target_lng: Optional[float] = None
    target_lat: Optional[float] = None
    description: Optional[str] = ""
    cargo_manifest: Optional[Any] = None
    cargo_weight_kg: Optional[float] = 0
    delivery_status: Optional[str] = "pending"
    recon_images: Optional[Any] = None
    recon_videos: Optional[Any] = None
    route_analysis: Optional[str] = None
    route_analysis_data: Optional[Any] = None
    waypoints: Optional[Any] = None
    planned_distance_m: Optional[float] = 0
    actual_distance_m: Optional[float] = 0
    status: str = "pending"
    assigned_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    abort_reason: Optional[str] = None

    class Config:
        from_attributes = True


class MissionComplete(BaseModel):
    route_analysis: Optional[str] = None
    route_analysis_data: Optional[Any] = None
    recon_images: Optional[List[Any]] = None
    delivery_status: Optional[str] = None


# ---- 巡逻仿真 ----
class PatrolSimCreate(BaseModel):
    drone_id_str: Optional[str] = "无人机-01"
    canvas_width: Optional[int] = 1000
    canvas_height: Optional[int] = 660
    row_count: Optional[int] = 9


class PatrolSimStep(BaseModel):
    sim: Any = Field(..., description="仿真状态")
    dt: Optional[float] = 1.0
    survivors: Optional[List[Any]] = None


# ---- 物资投送 ----
class DeliveryRequest(BaseModel):
    hotspot_id: int
    custom_manifest: Optional[List[Any]] = None


class DeliveryConfirm(BaseModel):
    received_count: int
    received_by: Optional[str] = ""
    note: Optional[str] = ""


class DeliveryOut(BaseModel):
    id: int
    mission_id: Optional[int] = None
    drone_id_str: Optional[str] = ""
    target_location: str
    target_lng: Optional[float] = None
    target_lat: Optional[float] = None
    manifest: Optional[Any] = None
    total_weight_kg: Optional[float] = 0
    total_items: Optional[int] = 0
    category_summary: Optional[Any] = None
    status: str = "pending"
    priority: str = "P1"
    drop_method: Optional[str] = "hover_drop"
    drop_altitude_m: Optional[float] = 5
    drop_accuracy_m: Optional[float] = None
    requested_at: Optional[str] = None
    delivered_at: Optional[str] = None
    confirmed_at: Optional[str] = None
    received_by: Optional[str] = ""
    received_count: Optional[int] = None
    shortage_count: Optional[int] = 0
    fail_reason: Optional[str] = None

    class Config:
        from_attributes = True


class DeliveryPlan(BaseModel):
    delivery_id: int
    drone_id_str: Optional[str] = None


# ---- 侦察 ----
class ReconCreate(BaseModel):
    area_name: str
    center_lng: float
    center_lat: float
    drone_id_str: Optional[str] = None
    hotspot_id: Optional[int] = None


class ReconImageUpload(BaseModel):
    url: str
    taken_at: Optional[str] = None
    lng: Optional[float] = None
    lat: Optional[float] = None
    alt: Optional[float] = 120
    heading: Optional[float] = 0
    note: Optional[str] = ""


class ReconAnalyze(BaseModel):
    image_b64: Optional[str] = None
    context_data: Optional[Any] = None


class ReconOut(BaseModel):
    id: int
    mission_id: Optional[int] = None
    drone_id_str: Optional[str] = ""
    area_name: str
    center_lng: Optional[float] = None
    center_lat: Optional[float] = None
    coverage_sqkm: Optional[float] = 0
    images: Optional[Any] = None
    videos: Optional[Any] = None
    thermal_images: Optional[Any] = None
    lidar_point_count: Optional[int] = 0
    route_analysis: Optional[str] = None
    route_assessment: Optional[Any] = None
    discovered_elements: Optional[Any] = None
    survivor_signals: Optional[Any] = None
    status: str = "pending"
    analyzed_at: Optional[str] = None
    analyzed_by: Optional[str] = "Qwen-VL"

    class Config:
        from_attributes = True
