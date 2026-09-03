"""
无人机服务
对应无人机空中救援模块：机队管理 / 遥测处理 / 任务调度 / 巡逻仿真

保留并迁移演示版 (代码1.2-ai.html) 的巡逻动画核心逻辑：
- 蛇形扫描模式（zigzag）
- 激光点云生成
- 热成像生命探测
- 电量耗电模型
- DRONE_TELEMETRY_SCHEMA 遥测协议

扩展为多机支持 + 三种任务类型（巡逻/物资/侦察）
"""
import math
import time
import random
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models.drone import Drone, DroneMission


# ============================================================
# 遥测协议（与演示版 DRONE_TELEMETRY_SCHEMA 完全兼容）
# ============================================================
"""
DRONE_TELEMETRY_SCHEMA —— 标准遥测帧契约（真机接入的唯一数据协议）
{
  id:       string,   // 无人机编号，如 '无人机-01'
  x:        number,   // 地图坐标 x（仿真用画布坐标；真机用经度）
  y:        number,   // 地图坐标 y（仿真用画布坐标；真机用纬度）
  heading:  number,   // 航向（仿真 1/-1；真机为角度 0-360）
  battery:  number,   // 电量百分比 0-100
  mode:     string,   // 飞行模式：'search'/'supply'/'recon'/'standby'/'returning'
  payload:  any       // 载荷数据（激光雷达 / 热成像 / 物资 / 相机等，透传）
}
真机可经 大疆 Cloud API / MAVLink 转发为本格式，POST 至 /drone/telemetry
"""


class DroneService:
    """无人机机队管理服务"""

    # ---- 仿真参数（从演示版迁移） ----
    SIM_SPEED = 3.1           # 飞行速度 px/帧
    SIM_BATTERY_DRAIN = 0.006 # 每帧耗电百分比
    SIM_DISCOVER_RADIUS = 75  # 生命探测半径 px
    SIM_LIDAR_PER_FRAME = 3   # 每帧激光点云点数
    SIM_LIDAR_MAX = 6000      # 点云上限
    SIM_SCAN_RADIUS = 70      # 扫描圈半径 px

    # ---- 机队管理 ----

    @staticmethod
    def get_fleet(db: Session) -> list:
        """获取机队列表"""
        drones = db.query(Drone).order_by(Drone.id).all()
        return drones

    @staticmethod
    def get_drone(db: Session, drone_id_str: str) -> Optional[Drone]:
        """获取单台无人机"""
        return db.query(Drone).filter(Drone.drone_id_str == drone_id_str).first()

    @staticmethod
    def register_drone(db: Session, data: dict) -> Drone:
        """注册新无人机"""
        drone = Drone(
            drone_id_str=data["drone_id_str"],
            call_sign=data.get("call_sign", ""),
            model=data.get("model", ""),
            capabilities=data.get("capabilities", ["search"]),
            max_payload_kg=data.get("max_payload_kg", 0),
            max_flight_min=data.get("max_flight_min", 30),
            max_speed_ms=data.get("max_speed_ms", 15),
            home_base=data.get("home_base", ""),
            home_lng=data.get("home_lng"),
            home_lat=data.get("home_lat"),
            is_simulated=data.get("is_simulated", True),
            status="standby",
            battery=100.0,
        )
        db.add(drone)
        db.commit()
        db.refresh(drone)
        return drone

    @staticmethod
    def get_fleet_status_summary(db: Session) -> dict:
        """机队状态汇总"""
        drones = db.query(Drone).all()
        total = len(drones)
        by_status = {}
        for d in drones:
            by_status[d.status] = by_status.get(d.status, 0) + 1
        return {
            "total": total,
            "standby": by_status.get("standby", 0),
            "searching": by_status.get("searching", 0),
            "supplying": by_status.get("supplying", 0),
            "recon": by_status.get("recon", 0),
            "returning": by_status.get("returning", 0),
            "charging": by_status.get("charging", 0),
            "offline": by_status.get("offline", 0),
            "avg_battery": sum(d.battery for d in drones) / total if total else 0,
        }

    # ---- 遥测处理 ----

    @staticmethod
    def apply_telemetry(db: Session, frame: dict) -> Optional[Drone]:
        """
        处理遥测帧（仿真与真机统一入口）
        对应演示版 applyTelemetry()
        """
        drone_id = frame.get("id")
        if not drone_id:
            return None

        drone = db.query(Drone).filter(Drone.drone_id_str == drone_id).first()
        if not drone:
            return None

        # 更新位置
        if "x" in frame:
            drone.longitude = frame["x"]  # 仿真时为画布坐标
        if "y" in frame:
            drone.latitude = frame["y"]
        if "heading" in frame:
            drone.heading = frame["heading"]
        if "battery" in frame:
            drone.battery = max(0, min(100, frame["battery"]))
        if "mode" in frame:
            mode_map = {
                "search": "searching",
                "supply": "supplying",
                "recon": "recon",
                "standby": "standby",
                "returning": "returning",
            }
            drone.status = mode_map.get(frame["mode"], drone.status)
        if "payload" in frame:
            drone.payload_detail = frame["payload"]

        drone.last_telemetry_at = datetime.now()
        db.commit()
        db.refresh(drone)
        return drone

    @staticmethod
    def get_telemetry(db: Session, drone_id_str: str) -> Optional[dict]:
        """获取无人机遥测数据"""
        drone = db.query(Drone).filter(Drone.drone_id_str == drone_id_str).first()
        if not drone:
            return None
        return {
            "id": drone.drone_id_str,
            "x": drone.longitude,
            "y": drone.latitude,
            "heading": drone.heading,
            "battery": drone.battery,
            "mode": drone.status,
            "altitude_m": drone.altitude_m,
            "speed_ms": drone.speed_ms,
            "payload": drone.payload_detail,
            "last_telemetry_at": drone.last_telemetry_at.isoformat() if drone.last_telemetry_at else None,
        }

    # ---- 巡逻仿真引擎（从演示版迁移） ----

    @staticmethod
    def create_patrol_simulation(drone_id_str: str = "无人机-01",
                                  canvas_width: int = 1000,
                                  canvas_height: int = 660,
                                  row_count: int = 9) -> dict:
        """
        创建巡逻仿真会话
        返回仿真状态，前端可据此驱动画布动画

        迁移自演示版：
        - S.drone = {active, x, dir, battery}
        - ROWS = [64, 130, 196, 262, 328, 394, 460, 526, 592]
        - 蛇形扫描模式
        """
        row_spacing = (canvas_height - 64) / max(row_count - 1, 1)
        rows = [round(64 + i * row_spacing) for i in range(row_count)]

        return {
            "drone_id": drone_id_str,
            "active": False,
            "x": -30,
            "y": rows[0],
            "dir": 1,
            "battery": 100,
            "coverage": 0,
            "row_idx": 0,
            "rows": rows,
            "canvas_width": canvas_width,
            "canvas_height": canvas_height,
            "scan_radius": DroneService.SIM_SCAN_RADIUS,
            "discover_radius": DroneService.SIM_DISCOVER_RADIUS,
            "lidar_points": [],
            "discovered_survivors": [],
            "speed": DroneService.SIM_SPEED,
            "battery_drain": DroneService.SIM_BATTERY_DRAIN,
            "lidar_per_frame": DroneService.SIM_LIDAR_PER_FRAME,
            "lidar_max": DroneService.SIM_LIDAR_MAX,
            "temperature": 22.4,
            "started_at": None,
        }

    @staticmethod
    def step_patrol_simulation(sim: dict, dt: float = 1.0, survivors: list = None) -> dict:
        """
        推进巡逻仿真一帧
        对应演示版 update() 中的无人机运动逻辑

        参数：
            sim: 仿真状态（由 create_patrol_simulation 创建）
            dt: 帧间隔（归一化到 16.67ms = 1.0）
            survivors: 被困人员列表 [{id, x, y, discovered}]

        返回更新后的 sim，以及本帧事件列表
        """
        events = []

        if not sim["active"]:
            return sim, events

        # 移动
        sim["x"] += DroneService.SIM_SPEED * sim["dir"] * dt

        # 耗电
        sim["battery"] = max(5, sim["battery"] - DroneService.SIM_BATTERY_DRAIN * dt)

        # 生成激光点云
        for _ in range(DroneService.SIM_LIDAR_PER_FRAME):
            angle = random.random() * math.pi * 2
            r = math.sqrt(random.random()) * DroneService.SIM_SCAN_RADIUS
            sim["lidar_points"].append({
                "x": sim["x"] + math.cos(angle) * r,
                "y": sim["rows"][sim["row_idx"]] + math.sin(angle) * r,
            })
        if len(sim["lidar_points"]) > DroneService.SIM_LIDAR_MAX:
            sim["lidar_points"] = sim["lidar_points"][-DroneService.SIM_LIDAR_MAX:]

        # 热成像温度波动
        sim["temperature"] = round(34 + math.sin(time.time() / 1.5) * 1.6 + random.random(), 1)

        # 生命探测
        if survivors:
            current_y = sim["rows"][sim["row_idx"]]
            for sv in survivors:
                if not sv.get("discovered"):
                    dist = math.hypot(sv["x"] - sim["x"], sv["y"] - current_y)
                    if dist < DroneService.SIM_DISCOVER_RADIUS:
                        sv["discovered"] = True
                        sim["discovered_survivors"].append(sv["id"])
                        events.append({
                            "type": "survivor_discovered",
                            "survivor_id": sv["id"],
                            "x": sv["x"],
                            "y": sv["y"],
                            "message": f"热成像发现疑似生命迹象 {sv['id']}",
                        })

        # 边界检测 → 换行
        mw = sim["canvas_width"]
        if (sim["dir"] == 1 and sim["x"] > mw + 30) or \
           (sim["dir"] == -1 and sim["x"] < -30):
            sim["row_idx"] += 1
            if sim["row_idx"] >= len(sim["rows"]):
                sim["active"] = False
                sim["coverage"] = 100
                events.append({
                    "type": "scan_complete",
                    "message": "全域搜索完成 · 覆盖率 100% · 现场数字孪生已更新",
                })
            else:
                sim["dir"] *= -1
                sim["x"] = -30 if sim["dir"] == 1 else mw + 30

        # 覆盖率
        mw = sim["canvas_width"]
        prog = min(1, sim["x"] / mw) if sim["dir"] == 1 else min(1, (mw - sim["x"]) / mw)
        sim["coverage"] = round(min(100, ((sim["row_idx"] + prog) / len(sim["rows"])) * 100), 1)

        # 生成遥测帧
        sim["telemetry_frame"] = {
            "id": sim["drone_id"],
            "x": round(sim["x"], 1),
            "y": sim["rows"][sim["row_idx"]],
            "heading": sim["dir"],
            "battery": round(sim["battery"], 1),
            "mode": "search",
            "payload": {
                "lidar_points": len(sim["lidar_points"]),
                "temperature": sim["temperature"],
                "coverage": sim["coverage"],
                "row_idx": sim["row_idx"],
                "row_total": len(sim["rows"]),
            },
        }

        return sim, events

    @staticmethod
    def start_patrol(sim: dict) -> dict:
        """启动巡逻（对应演示版 btnScan.onclick）"""
        sim["active"] = True
        sim["x"] = -30
        sim["dir"] = 1
        sim["battery"] = 100
        sim["coverage"] = 0
        sim["row_idx"] = 0
        sim["lidar_points"] = []
        sim["discovered_survivors"] = []
        sim["started_at"] = datetime.now().isoformat()
        return sim

    @staticmethod
    def stop_patrol(sim: dict) -> dict:
        """停止巡逻"""
        sim["active"] = False
        return sim

    # ---- 任务调度 ----

    @staticmethod
    def assign_mission(db: Session, drone_id_str: str, mission_data: dict) -> Optional[DroneMission]:
        """给无人机分配任务"""
        drone = db.query(Drone).filter(Drone.drone_id_str == drone_id_str).first()
        if not drone:
            return None

        if drone.status not in ("standby", "charging"):
            return None  # 无人机忙

        mission = DroneMission(
            mission_type=mission_data.get("mission_type", "search"),
            target_location=mission_data.get("target_location", ""),
            target_lng=mission_data.get("target_lng"),
            target_lat=mission_data.get("target_lat"),
            description=mission_data.get("description", ""),
            cargo_manifest=mission_data.get("cargo_manifest"),
            cargo_weight_kg=mission_data.get("cargo_weight_kg", 0),
            waypoints=mission_data.get("waypoints", []),
            planned_distance_m=mission_data.get("planned_distance_m", 0),
            disaster_id=mission_data.get("disaster_id"),
            hotspot_id=mission_data.get("hotspot_id"),
            status="assigned",
            assigned_at=datetime.now(),
        )
        db.add(mission)
        db.flush()

        # 更新无人机状态
        drone.current_mission_id = mission.id
        type_status_map = {
            "search": "searching",
            "supply": "supplying",
            "recon": "recon",
            "comm_relay": "searching",
        }
        drone.status = type_status_map.get(mission.mission_type, "searching")
        if mission.mission_type == "supply":
            drone.payload_type = "cargo"
            drone.payload_detail = mission.cargo_manifest
        elif mission.mission_type == "recon":
            drone.payload_type = "camera"
        elif mission.mission_type == "search":
            drone.payload_type = "thermal"

        db.commit()
        db.refresh(mission)
        return mission

    @staticmethod
    def get_active_missions(db: Session) -> list:
        """获取进行中的任务"""
        return db.query(DroneMission).filter(
            DroneMission.status.in_(["assigned", "in_progress"])
        ).order_by(DroneMission.assigned_at.desc()).all()

    @staticmethod
    def complete_mission(db: Session, mission_id: int, result: dict = None) -> Optional[DroneMission]:
        """完成任务"""
        mission = db.query(DroneMission).filter(DroneMission.id == mission_id).first()
        if not mission:
            return None

        mission.status = "completed"
        mission.completed_at = datetime.now()

        result = result or {}
        if "route_analysis" in result:
            mission.route_analysis = result["route_analysis"]
        if "route_analysis_data" in result:
            mission.route_analysis_data = result["route_analysis_data"]
        if "recon_images" in result:
            mission.recon_images = result["recon_images"]
        if "delivery_status" in result:
            mission.delivery_status = result["delivery_status"]

        # 释放无人机
        if mission.drone_id:
            drone = db.query(Drone).filter(Drone.id == mission.drone_id).first()
            if drone:
                drone.status = "returning"
                drone.current_mission_id = None
                drone.payload_type = "none"
                drone.payload_detail = None

        db.commit()
        db.refresh(mission)
        return mission

    @staticmethod
    def abort_mission(db: Session, mission_id: int, reason: str = "") -> Optional[DroneMission]:
        """中止任务"""
        mission = db.query(DroneMission).filter(DroneMission.id == mission_id).first()
        if not mission:
            return None

        mission.status = "aborted"
        mission.abort_reason = reason
        mission.completed_at = datetime.now()

        if mission.drone_id:
            drone = db.query(Drone).filter(Drone.id == mission.drone_id).first()
            if drone:
                drone.status = "returning"
                drone.current_mission_id = None

        db.commit()
        db.refresh(mission)
        return mission

    # ---- 仿真初始化（演示用） ----

    @staticmethod
    def init_sim_fleet(db: Session):
        """初始化仿真机队（演示用，3 台无人机）"""
        existing = db.query(Drone).count()
        if existing > 0:
            return

        drones = [
            Drone(
                drone_id_str="无人机-01",
                call_sign="苍鹰-01",
                model="大疆 M300 RTK",
                capabilities=["search", "recon"],
                max_payload_kg=2.7,
                max_flight_min=55,
                max_speed_ms=23,
                home_base="前线指挥部",
                home_lng=95.95,
                home_lat=21.20,
                is_simulated=True,
                status="standby",
                battery=100,
            ),
            Drone(
                drone_id_str="无人机-02",
                call_sign="苍鹰-02",
                model="大疆 M350 RTK",
                capabilities=["supply"],
                max_payload_kg=5.0,
                max_flight_min=55,
                max_speed_ms=23,
                home_base="物资集散点",
                home_lng=95.96,
                home_lat=21.21,
                is_simulated=True,
                status="standby",
                battery=100,
            ),
            Drone(
                drone_id_str="无人机-03",
                call_sign="翼龙-2H",
                model="翼龙-2H 通信中继型",
                capabilities=["comm_relay", "recon"],
                max_payload_kg=0,
                max_flight_min=480,
                max_speed_ms=30,
                home_base="后方机场",
                home_lng=96.10,
                home_lat=21.30,
                is_simulated=True,
                status="standby",
                battery=100,
            ),
        ]
        for d in drones:
            db.add(d)
        db.commit()
