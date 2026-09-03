"""
无人机模型
对应无人机空中救援模块：机队管理 / 物资运输 / 空中侦察
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class Drone(Base):
    """无人机（机队管理）"""
    __tablename__ = "drones"

    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(String(50), unique=True, nullable=False, index=True)  # 无人机-01
    call_sign = Column(String(50))                            # 呼号：如"翼龙-2H"
    model = Column(String(100))                               # 机型：大疆M300/翼龙-2H等

    # 任务能力
    capabilities = Column(JSON)  # ["search", "supply", "recon", "comm_relay"]
    max_payload_kg = Column(Float, default=0)                 # 最大载重 kg
    max_flight_min = Column(Float, default=30)                # 最大续航分钟
    max_speed_ms = Column(Float, default=15)                  # 最大速度 m/s

    # 实时状态（由遥测更新）
    status = Column(String(20), default="standby")            # standby/searching/supplying/recon/returning/charging/offline
    battery = Column(Float, default=100)                      # 电量百分比 0-100
    longitude = Column(Float)                                 # 经度
    latitude = Column(Float)                                  # 纬度
    altitude_m = Column(Float, default=0)                     # 飞行高度 m
    speed_ms = Column(Float, default=0)                       # 当前速度 m/s
    heading = Column(Float, default=0)                        # 航向角 0-360

    # 当前任务
    current_mission_id = Column(Integer, ForeignKey("drone_missions.id"), nullable=True)
    home_base = Column(String(100))                           # 起降点名称
    home_lng = Column(Float)
    home_lat = Column(Float)

    # 载荷信息
    payload_type = Column(String(30))                         # none/cargo/camera/lidar/thermal/comm_relay
    payload_detail = Column(JSON)                             # 载荷明细：物资清单 / 相机参数等

    # 仿真标记
    is_simulated = Column(Boolean, default=True)              # 是否仿真（数字孪生）
    last_telemetry_at = Column(DateTime)                      # 最后遥测时间

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DroneMission(Base):
    """无人机任务"""
    __tablename__ = "drone_missions"

    id = Column(Integer, primary_key=True, index=True)
    mission_type = Column(String(20), nullable=False, index=True)  # search/supply/recon/comm_relay
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=True)

    # 任务目标
    target_location = Column(String(100))                     # 目标地点
    target_lng = Column(Float)
    target_lat = Column(Float)
    description = Column(Text)                                # 任务描述

    # 物资运输专属
    cargo_manifest = Column(JSON)                             # [{"item":"帐篷","qty":5,"weight_kg":2}]
    cargo_weight_kg = Column(Float, default=0)                # 总载重
    delivery_status = Column(String(20), default="pending")   # pending/loading/en_route/delivered/failed

    # 侦察专属
    recon_images = Column(JSON)                               # [{"url":"...","taken_at":"...","lat":...,"lng":...}]
    recon_videos = Column(JSON)                               # [{"url":"...","duration_s":120}]
    route_analysis = Column(Text)                             # AI 路线分析结果
    route_analysis_data = Column(JSON)                        # 结构化路线分析

    # 航线
    waypoints = Column(JSON)                                  # [{"lng":...,"lat":...,"alt":...,"action":"hover"}]
    planned_distance_m = Column(Float, default=0)             # 规划航程 m
    actual_distance_m = Column(Float, default=0)              # 实际航程 m

    # 时间线
    status = Column(String(20), default="pending")            # pending/assigned/in_progress/completed/aborted
    assigned_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    abort_reason = Column(String(200))                        # 中止原因

    # 关联
    disaster_id = Column(Integer, ForeignKey("disasters.id"), nullable=True)
    hotspot_id = Column(Integer, ForeignKey("disaster_hotspots.id"), nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
