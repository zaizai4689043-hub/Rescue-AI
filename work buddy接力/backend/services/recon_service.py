"""
空中侦察服务
对应无人机空中救援模块 - 灾情侦察 / 路线研判

功能：
1. 创建侦察任务（指定区域 → 自动分配无人机）
2. 管理侦察素材（图片/视频/热成像/激光点云）
3. AI 路线分析（Qwen-VL 分析航拍画面 → 判断道路可通行性）
4. 路线研判输出（可通行路线 / 阻断路线 / 危险区域 / 推荐路线）
5. 灾情要素识别（建筑倒塌/道路损毁/生命迹象/次生灾害）

注：此模块为低优先级，放在物资运输之后实现
"""
import json
import math
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models.drone import Drone, DroneMission
from models.aerial_recon import AerialRecon
from models.disaster_hotspot import DisasterHotspot
from services.ai_client import ai_client


class ReconService:
    """空中侦察服务"""

    @staticmethod
    def create_recon_mission(db: Session, area_name: str, center_lng: float,
                             center_lat: float, drone_id_str: str = None,
                             hotspot_id: int = None) -> Optional[dict]:
        """创建侦察任务"""
        # 选择无人机
        drone = None
        if drone_id_str:
            drone = db.query(Drone).filter(Drone.drone_id_str == drone_id_str).first()
        if not drone:
            # 优先选有 recon 能力的
            drones = db.query(Drone).filter(
                Drone.status == "standby"
            ).all()
            for d in drones:
                if d.capabilities and "recon" in d.capabilities:
                    drone = d
                    break
            if not drone and drones:
                drone = drones[0]
        if not drone:
            return {"error": "no_available_drone"}

        # 创建任务
        mission = DroneMission(
            mission_type="recon",
            drone_id=drone.id,
            target_location=area_name,
            target_lng=center_lng,
            target_lat=center_lat,
            description=f"空中侦察 → {area_name}",
            waypoints=[
                {"lng": drone.home_lng, "lat": drone.home_lat, "alt": 0, "action": "takeoff"},
                {"lng": drone.home_lng, "lat": drone.home_lat, "alt": 120, "action": "climb"},
                {"lng": center_lng, "lat": center_lat, "alt": 120, "action": "cruise"},
                {"lng": center_lng, "lat": center_lat, "alt": 120, "action": "survey_start"},
                {"lng": center_lng + 0.01, "lat": center_lat + 0.01, "alt": 120, "action": "survey"},
                {"lng": center_lng - 0.01, "lat": center_lat + 0.01, "alt": 120, "action": "survey"},
                {"lng": center_lng - 0.01, "lat": center_lat - 0.01, "alt": 120, "action": "survey"},
                {"lng": center_lng + 0.01, "lat": center_lat - 0.01, "alt": 120, "action": "survey_end"},
                {"lng": drone.home_lng, "lat": drone.home_lat, "alt": 120, "action": "return"},
                {"lng": drone.home_lng, "lat": drone.home_lat, "alt": 0, "action": "land"},
            ],
            status="assigned",
            assigned_at=datetime.now(),
        )
        db.add(mission)
        db.flush()

        # 创建侦察记录
        recon = AerialRecon(
            mission_id=mission.id,
            drone_id_str=drone.drone_id_str,
            area_name=area_name,
            center_lng=center_lng,
            center_lat=center_lat,
            coverage_sqkm=4.0,  # 默认覆盖 4 平方公里
            images=[],
            videos=[],
            thermal_images=[],
            lidar_point_count=0,
            status="pending",
        )
        db.add(recon)

        # 更新无人机
        drone.status = "recon"
        drone.current_mission_id = mission.id
        drone.payload_type = "camera"

        if hotspot_id:
            mission.hotspot_id = hotspot_id
            recon.hotspot_id = hotspot_id

        db.commit()
        db.refresh(mission)
        db.refresh(recon)

        return {
            "mission_id": mission.id,
            "recon_id": recon.id,
            "drone_id": drone.drone_id_str,
            "area_name": area_name,
            "waypoints": mission.waypoints,
        }

    @staticmethod
    def upload_recon_image(db: Session, recon_id: int, image_data: dict) -> Optional[AerialRecon]:
        """上传侦察图片"""
        recon = db.query(AerialRecon).filter(AerialRecon.id == recon_id).first()
        if not recon:
            return None

        images = recon.images or []
        images.append({
            "url": image_data.get("url", ""),
            "taken_at": image_data.get("taken_at", datetime.now().isoformat()),
            "lng": image_data.get("lng"),
            "lat": image_data.get("lat"),
            "alt": image_data.get("alt", 120),
            "heading": image_data.get("heading", 0),
            "note": image_data.get("note", ""),
        })
        recon.images = images

        if recon.status == "pending":
            recon.status = "in_progress"

        db.commit()
        db.refresh(recon)
        return recon

    @staticmethod
    def analyze_route_with_ai(db: Session, recon_id: int, image_b64: str = None,
                              context_data: dict = None) -> Optional[AerialRecon]:
        """
        AI 路线分析
        使用 Qwen-VL 分析航拍画面，判断道路可通行性

        参数：
            image_b64: 航拍图片 base64（可选，无则用文本分析）
            context_data: 上下文信息（热点数据、微博情报等）
        """
        recon = db.query(AerialRecon).filter(AerialRecon.id == recon_id).first()
        if not recon:
            return None

        context = context_data or {}

        if image_b64:
            # 视觉分析
            prompt = """你是地震灾后道路通行性研判专家。这是无人机航拍的灾区画面。
请分析并返回严格 JSON：
{
  "accessible_routes": [
    {"from":"起点","to":"终点","via":"路线描述","status":"clear|caution","estimated_time_min":45,"notes":"路面状态"}
  ],
  "blocked_routes": [
    {"from":"起点","to":"终点","via":"路线描述","block_type":"桥梁断裂|道路塌方|建筑倒塌阻断|落石|泥石流","block_location":"位置","detour":"绕行方案"}
  ],
  "hazard_zones": [
    {"location":"位置","hazard_type":"滑坡风险|堰塞湖|建筑倾斜|燃气泄漏","severity":"high|medium|low","advice":"建议措施"}
  ],
  "building_damage": {
    "collapse_count": 0,
    "severe_count": 0,
    "moderate_count": 0,
    "minor_count": 0
  },
  "survivor_signals": [
    {"location":"位置描述","signal_type":"SOS标志|呼救声|热成像异常","confidence":0.0-1.0}
  ],
  "recommended_routes": [
    {"route":"路线名","reason":"推荐理由","priority":1}
  ],
  "overall_assessment": "总体路况评估（100字内）"
}
只返回 JSON。"""

            result = ai_client.vl_chat_json(prompt, image_b64, temperature=0.3, timeout=20)
        else:
            # 文本分析（基于情报数据）
            prompt = f"""你是地震灾后道路通行性研判专家。请基于以下情报分析灾区道路可通行性。

侦察区域：{recon.area_name}
侦察中心坐标：{recon.center_lng}, {recon.center_lat}

相关灾情情报：
{json.dumps(context, ensure_ascii=False, indent=2)}

请返回严格 JSON：
{{
  "accessible_routes": [
    {{"from":"起点","to":"终点","via":"路线描述","status":"clear|caution","estimated_time_min":45,"notes":"路面状态"}}
  ],
  "blocked_routes": [
    {{"from":"起点","to":"终点","via":"路线描述","block_type":"桥梁断裂|道路塌方|建筑倒塌阻断|落石|泥石流","block_location":"位置","detour":"绕行方案"}}
  ],
  "hazard_zones": [
    {{"location":"位置","hazard_type":"滑坡风险|堰塞湖|建筑倾斜|燃气泄漏","severity":"high|medium|low","advice":"建议措施"}}
  ],
  "recommended_routes": [
    {{"route":"路线名","reason":"推荐理由","priority":1}}
  ],
  "overall_assessment": "总体路况评估（100字内）"
}}
只返回 JSON。"""

            result = ai_client.chat_json(prompt, temperature=0.4, timeout=12)

        if result:
            recon.route_assessment = result
            recon.route_analysis = result.get("overall_assessment", "")
            recon.discovered_elements = _extract_discovered_elements(result)
            recon.survivor_signals = result.get("survivor_signals", [])
            recon.status = "analyzed"
            recon.analyzed_at = datetime.now()
            recon.analyzed_by = "Qwen-VL" if image_b64 else "Qwen3.8-Max"
        else:
            # 降级：使用规则生成基础分析
            recon.route_analysis = "AI 分析不可用，建议人工查看航拍画面。"
            recon.route_assessment = _fallback_route_analysis(context)
            recon.status = "analyzed"
            recon.analyzed_at = datetime.now()
            recon.analyzed_by = "rule_based"

        db.commit()
        db.refresh(recon)
        return recon

    @staticmethod
    def get_recon_list(db: Session, area_name: str = None) -> list:
        """获取侦察记录列表"""
        query = db.query(AerialRecon)
        if area_name:
            query = query.filter(AerialRecon.area_name.contains(area_name))
        return query.order_by(AerialRecon.created_at.desc()).all()

    @staticmethod
    def get_route_summary(db: Session) -> dict:
        """路线研判汇总"""
        recons = db.query(AerialRecon).filter(
            AerialRecon.status == "analyzed"
        ).all()

        all_accessible = []
        all_blocked = []
        all_hazards = []
        all_recommended = []

        for r in recons:
            if r.route_assessment:
                all_accessible.extend(r.route_assessment.get("accessible_routes", []))
                all_blocked.extend(r.route_assessment.get("blocked_routes", []))
                all_hazards.extend(r.route_assessment.get("hazard_zones", []))
                all_recommended.extend(r.route_assessment.get("recommended_routes", []))

        return {
            "total_recons": len(recons),
            "accessible_routes": all_accessible,
            "blocked_routes": all_blocked,
            "hazard_zones": all_hazards,
            "recommended_routes": sorted(all_recommended, key=lambda x: x.get("priority", 99)),
        }


def _extract_discovered_elements(route_assessment: dict) -> list:
    """从路线研判结果中提取发现的灾情要素"""
    elements = []
    building = route_assessment.get("building_damage", {})
    if building:
        total_collapse = building.get("collapse_count", 0)
        if total_collapse > 0:
            elements.append({
                "type": "building_collapse",
                "count": total_collapse,
                "severity": "high",
            })
        severe = building.get("severe_count", 0)
        if severe > 0:
            elements.append({
                "type": "building_severe_damage",
                "count": severe,
                "severity": "high",
            })

    blocked = route_assessment.get("blocked_routes", [])
    if blocked:
        elements.append({
            "type": "road_damage",
            "count": len(blocked),
            "severity": "high",
            "details": [{"location": b.get("block_location", ""), "type": b.get("block_type", "")} for b in blocked],
        })

    hazards = route_assessment.get("hazard_zones", [])
    for h in hazards:
        elements.append({
            "type": h.get("hazard_type", "unknown"),
            "location": h.get("location", ""),
            "severity": h.get("severity", "medium"),
            "advice": h.get("advice", ""),
        })

    survivors = route_assessment.get("survivor_signals", [])
    for s in survivors:
        elements.append({
            "type": "survivor_signal",
            "location": s.get("location", ""),
            "signal_type": s.get("signal_type", ""),
            "confidence": s.get("confidence", 0.5),
        })

    return elements


def _fallback_route_analysis(context: dict) -> dict:
    """规则降级：基于情报生成基础路线分析"""
    hotspots = context.get("hotspots", [])
    accessible = []
    blocked = []
    hazards = []

    for h in hotspots:
        if h.get("road_accessible", True):
            accessible.append({
                "from": "指挥部",
                "to": h.get("location_name", ""),
                "via": "主干道",
                "status": "caution",
                "estimated_time_min": 30,
                "notes": "社媒反馈道路可通行，建议谨慎前进",
            })
        else:
            blocked.append({
                "from": "指挥部",
                "to": h.get("location_name", ""),
                "via": "主干道",
                "block_type": "道路中断",
                "block_location": h.get("location_name", ""),
                "detour": "需无人机侦察后确定绕行路线",
            })

    return {
        "accessible_routes": accessible,
        "blocked_routes": blocked,
        "hazard_zones": hazards,
        "recommended_routes": [
            {"route": r["to"], "reason": "社媒情报显示可通行", "priority": i + 1}
            for i, r in enumerate(accessible)
        ],
        "overall_assessment": "AI 视觉分析不可用，当前路线研判基于社媒情报规则生成，建议人工复核。",
    }
