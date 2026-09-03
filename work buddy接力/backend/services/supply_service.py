"""
物资运输服务
对应无人机空中救援模块 - 物资投送

功能：
1. 根据灾情热点优先级自动生成物资投送需求
2. 规划投送航线（起降点 → 目标区域 → 返航）
3. 载重约束检查（无人机载重 vs 物资重量）
4. 投送状态跟踪（装载 → 起飞 → 抵达 → 投送 → 确认）
5. AI 辅助物资清单规划（基于灾情类型推荐物资组合）
"""
import math
import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models.drone import Drone, DroneMission
from models.supply_delivery import SupplyDelivery
from models.disaster_hotspot import DisasterHotspot
from services.ai_client import ai_client


# ---- 物资分类 ----
SUPPLY_CATEGORIES = {
    "shelter": ["帐篷", "折叠床", "棉被", "防水布", "取暖炉"],
    "food": ["压缩饼干", "方便面", "自热米饭", "矿泉水", "婴幼儿食品"],
    "medical": ["急救包", "止血带", "夹板", "消炎药", "破伤风疫苗", "氧气袋"],
    "water": ["瓶装水", "净水片", "蓄水袋"],
    "lighting": ["手电筒", "应急灯", "发电机", "燃油"],
    "communication": ["对讲机", "卫星电话", "充电宝"],
    "rescue_tool": ["液压钳", "生命探测仪", "破拆工具", "支撑杆"],
}

# 标准物资包（按灾情优先级）
STANDARD_PACKAGES = {
    "P0": {
        "name": "紧急生命救援包",
        "items": [
            {"item": "急救包", "qty": 10, "weight_kg": 0.5, "category": "medical"},
            {"item": "生命探测仪", "qty": 2, "weight_kg": 3.0, "category": "rescue_tool"},
            {"item": "瓶装水", "qty": 24, "weight_kg": 0.5, "category": "water"},
            {"item": "压缩饼干", "qty": 20, "weight_kg": 0.1, "category": "food"},
        ],
    },
    "P1": {
        "name": "基本生存保障包",
        "items": [
            {"item": "帐篷", "qty": 5, "weight_kg": 8.0, "category": "shelter"},
            {"item": "瓶装水", "qty": 48, "weight_kg": 0.5, "category": "water"},
            {"item": "方便面", "qty": 30, "weight_kg": 0.1, "category": "food"},
            {"item": "急救包", "qty": 5, "weight_kg": 0.5, "category": "medical"},
            {"item": "手电筒", "qty": 10, "weight_kg": 0.2, "category": "lighting"},
        ],
    },
    "P2": {
        "name": "生活保障补充包",
        "items": [
            {"item": "棉被", "qty": 20, "weight_kg": 2.0, "category": "shelter"},
            {"item": "矿泉水", "qty": 48, "weight_kg": 0.5, "category": "water"},
            {"item": "自热米饭", "qty": 30, "weight_kg": 0.25, "category": "food"},
            {"item": "对讲机", "qty": 5, "weight_kg": 0.3, "category": "communication"},
        ],
    },
    "P3": {
        "name": "恢复重建支持包",
        "items": [
            {"item": "防水布", "qty": 20, "weight_kg": 1.5, "category": "shelter"},
            {"item": "发电机", "qty": 2, "weight_kg": 15.0, "category": "lighting"},
            {"item": "净水片", "qty": 100, "weight_kg": 0.01, "category": "water"},
        ],
    },
}


class SupplyService:
    """物资运输服务"""

    @staticmethod
    def haversine_distance(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
        """计算两点间距离（米）"""
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lng2 - lng1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def estimate_flight_time(distance_m: float, drone_speed_ms: float = 15) -> dict:
        """估算飞行时间"""
        one_way_s = distance_m / drone_speed_ms if drone_speed_ms > 0 else 0
        round_trip_s = one_way_s * 2 + 300  # 往返 + 5分钟投送时间
        return {
            "one_way_min": round(one_way_s / 60, 1),
            "round_trip_min": round(round_trip_s / 60, 1),
            "battery_needed_pct": round((round_trip_s / 60) * 0.8, 1),  # 约 0.8%/min
        }

    @staticmethod
    def get_standard_package(priority: str) -> dict:
        """获取标准物资包"""
        return STANDARD_PACKAGES.get(priority, STANDARD_PACKAGES["P1"])

    @staticmethod
    def select_drone_for_payload(db: Session, payload_kg: float, mission_type: str = "supply") -> Optional[Drone]:
        """选择载重足够的可用无人机"""
        drones = db.query(Drone).filter(
            Drone.status == "standby",
            Drone.max_payload_kg >= payload_kg,
        ).order_by(Drone.max_payload_kg.asc()).all()

        # 优先选有 supply 能力的
        for d in drones:
            if d.capabilities and "supply" in d.capabilities:
                return d
        return drones[0] if drones else None

    @staticmethod
    def create_delivery_request(db: Session, hotspot_id: int, custom_manifest: list = None) -> Optional[SupplyDelivery]:
        """根据灾情热点创建物资投送需求"""
        hotspot = db.query(DisasterHotspot).filter(DisasterHotspot.id == hotspot_id).first()
        if not hotspot:
            return None

        # 选择物资包
        priority = hotspot.priority_level or "P1"
        package = SupplyService.get_standard_package(priority)
        manifest = custom_manifest or package["items"]

        # 计算总重和总数
        total_weight = sum(item.get("weight_kg", 0) * item.get("qty", 1) for item in manifest)
        total_items = sum(item.get("qty", 0) for item in manifest)

        # 分类统计
        cat_summary = {}
        for item in manifest:
            cat = item.get("category", "other")
            cat_summary[cat] = cat_summary.get(cat, 0) + item.get("qty", 0)

        delivery = SupplyDelivery(
            target_location=hotspot.location_name,
            target_lng=hotspot.longitude,
            target_lat=hotspot.latitude,
            manifest=manifest,
            total_weight_kg=round(total_weight, 2),
            total_items=total_items,
            category_summary=cat_summary,
            status="pending",
            priority=priority,
            drop_method="hover_drop",
            drop_altitude_m=5,
            disaster_id=hotspot.disaster_id,
            hotspot_id=hotspot.id,
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        return delivery

    @staticmethod
    def plan_delivery_route(db: Session, delivery_id: int, drone_id_str: str = None) -> Optional[dict]:
        """规划投送航线"""
        delivery = db.query(SupplyDelivery).filter(SupplyDelivery.id == delivery_id).first()
        if not delivery:
            return None

        # 选择无人机
        drone = None
        if drone_id_str:
            drone = db.query(Drone).filter(Drone.drone_id_str == drone_id_str).first()
        if not drone:
            drone = SupplyService.select_drone_for_payload(db, delivery.total_weight_kg)
        if not drone:
            return {"error": "no_available_drone", "message": f"没有载重 ≥{delivery.total_weight_kg}kg 的可用无人机"}

        # 计算航线
        distance = SupplyService.haversine_distance(
            drone.home_lng, drone.home_lat,
            delivery.target_lng, delivery.target_lat
        )
        flight_time = SupplyService.estimate_flight_time(distance, drone.max_speed_ms)

        # 电量检查
        if drone.battery < flight_time["battery_needed_pct"]:
            return {"error": "battery_insufficient", "message": f"电量不足：需要{flight_time['battery_needed_pct']}%，当前{drone.battery}%"}

        # 航路点
        waypoints = [
            {"lng": drone.home_lng, "lat": drone.home_lat, "alt": 0, "action": "takeoff"},
            {"lng": drone.home_lng, "lat": drone.home_lat, "alt": 80, "action": "climb"},
            {"lng": delivery.target_lng, "lat": delivery.target_lat, "alt": 80, "action": "cruise"},
            {"lng": delivery.target_lng, "lat": delivery.target_lat, "alt": 5, "action": "descend"},
            {"lng": delivery.target_lng, "lat": delivery.target_lat, "alt": 5, "action": "drop"},
            {"lng": delivery.target_lng, "lat": delivery.target_lat, "alt": 80, "action": "climb"},
            {"lng": drone.home_lng, "lat": drone.home_lat, "alt": 80, "action": "return"},
            {"lng": drone.home_lng, "lat": drone.home_lat, "alt": 0, "action": "land"},
        ]

        # 创建任务
        mission = DroneMission(
            mission_type="supply",
            drone_id=drone.id,
            target_location=delivery.target_location,
            target_lng=delivery.target_lng,
            target_lat=delivery.target_lat,
            description=f"物资投送 → {delivery.target_location}（{delivery.priority}）",
            cargo_manifest=delivery.manifest,
            cargo_weight_kg=delivery.total_weight_kg,
            delivery_status="loading",
            waypoints=waypoints,
            planned_distance_m=round(distance * 2, 1),
            status="assigned",
            assigned_at=datetime.now(),
            disaster_id=delivery.disaster_id,
            hotspot_id=delivery.hotspot_id,
        )
        db.add(mission)
        db.flush()

        # 更新投送记录
        delivery.mission_id = mission.id
        delivery.drone_id_str = drone.drone_id_str
        delivery.status = "loading"
        delivery.loaded_at = datetime.now()

        # 更新无人机状态
        drone.status = "supplying"
        drone.current_mission_id = mission.id
        drone.payload_type = "cargo"
        drone.payload_detail = {
            "manifest": delivery.manifest,
            "total_weight_kg": delivery.total_weight_kg,
            "target": delivery.target_location,
        }

        db.commit()
        db.refresh(mission)

        return {
            "mission_id": mission.id,
            "drone_id": drone.drone_id_str,
            "delivery_id": delivery.id,
            "distance_m": round(distance, 1),
            "flight_time": flight_time,
            "waypoints": waypoints,
            "manifest": delivery.manifest,
            "total_weight_kg": delivery.total_weight_kg,
            "package_name": SupplyService.get_standard_package(delivery.priority).get("name", ""),
        }

    @staticmethod
    def confirm_delivery(db: Session, delivery_id: int, received_count: int,
                         received_by: str = "", note: str = "") -> Optional[SupplyDelivery]:
        """确认物资收到"""
        delivery = db.query(SupplyDelivery).filter(SupplyDelivery.id == delivery_id).first()
        if not delivery:
            return None

        delivery.status = "confirmed"
        delivery.confirmed_at = datetime.now()
        delivery.received_by = received_by
        delivery.received_count = received_count
        delivery.shortage_count = max(0, delivery.total_items - received_count)
        delivery.confirmation_note = note

        db.commit()
        db.refresh(delivery)
        return delivery

    @staticmethod
    def get_delivery_queue(db: Session) -> list:
        """获取投送队列"""
        return db.query(SupplyDelivery).filter(
            SupplyDelivery.status.in_(["pending", "loading", "en_route"])
        ).order_by(
            # P0 最先
            SupplyDelivery.priority.asc(),
            SupplyDelivery.requested_at.asc(),
        ).all()

    @staticmethod
    def get_delivery_stats(db: Session) -> dict:
        """投送统计"""
        deliveries = db.query(SupplyDelivery).all()
        total = len(deliveries)
        if total == 0:
            return {"total": 0}

        by_status = {}
        for d in deliveries:
            by_status[d.status] = by_status.get(d.status, 0) + 1

        return {
            "total": total,
            "pending": by_status.get("pending", 0),
            "in_transit": by_status.get("loading", 0) + by_status.get("en_route", 0),
            "delivered": by_status.get("delivered", 0) + by_status.get("confirmed", 0),
            "failed": by_status.get("failed", 0),
            "total_weight_kg": round(sum(d.total_weight_kg for d in deliveries), 1),
            "total_items": sum(d.total_items for d in deliveries),
        }

    @staticmethod
    def ai_plan_supplies(hotspot_data: dict, available_drones: list) -> Optional[dict]:
        """AI 辅助物资清单规划"""
        prompt = f"""你是应急救援物资调度专家。根据灾情热点信息，推荐最优无人机物资投送方案。

灾情热点信息：
{json.dumps(hotspot_data, ensure_ascii=False, indent=2)}

可用无人机：
{json.dumps(available_drones, ensure_ascii=False, indent=2)}

物资分类参考：shelter(帐篷/床/被)、food(压缩食品/水)、medical(急救包/药品)、
water(瓶装水/净水片)、lighting(照明/发电)、communication(对讲机/卫星电话)、rescue_tool(破拆/探测)

请返回严格 JSON：
{{
  "recommended_package": "物资包名称",
  "manifest": [
    {{"item": "物资名", "qty": 数量, "weight_kg": 单件重量, "category": "分类"}}
  ],
  "total_weight_kg": 总重,
  "drone_assignment": "推荐的无人机编号",
  "rationale": "方案理由（100字内）",
  "drop_method": "hover_drop|land|parachute",
  "drop_altitude_m": 投送高度
}}
只返回 JSON。"""
        return ai_client.chat_json(prompt, temperature=0.4, timeout=10)
