"""
动态优先级引擎
对应愿景 3：地图聚合 + 动态优先级排序

评分公式：
    base_score = urgency_score 归一化
    distress_boost = 呼救信号加权
    resource_penalty = 已有救援队 / 道路不可达 / 超时72h 扣减
    final_score = base × distress_boost × resource_penalty

输出：
    P0: score >= 0.8  → 立即派遣
    P1: 0.5 <= score < 0.8 → 优先派遣
    P2: 0.3 <= score < 0.5 → 常规搜救
    P3: score < 0.3 → 持续监测
"""
import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.disaster_hotspot import DisasterHotspot
from services.ai_client import ai_client


# 72 小时阈值（秒）
GOLDEN_WINDOW_HOURS = 72


class PriorityEngine:
    """动态优先级引擎"""

    @staticmethod
    def calculate_score(hotspot: DisasterHotspot) -> dict:
        """
        计算综合优先级评分
        返回 {score, level, factors}
        """
        factors = {}

        # ---- Step 1: 基础评分（归一化 urgency_score）----
        # urgency_score = post_count × avg_severity × avg_credibility
        # 归一化到 0-1：使用 log 压缩
        import math
        base = 1 - math.exp(-hotspot.urgency_score / 10)  # 指数衰减归一化
        factors["base_score"] = round(base, 3)
        factors["urgency_raw"] = hotspot.urgency_score

        # ---- Step 2: 呼救加权 ----
        distress_boost = 1.0
        if hotspot.distress_count > 0:
            # 每个呼救信号加 20%，上限 1.5
            distress_boost = min(1.5, 1.0 + hotspot.distress_count * 0.2)
        factors["distress_boost"] = distress_boost
        factors["distress_count"] = hotspot.distress_count

        # ---- Step 3: 资源约束扣减 ----
        penalties = 1.0

        # 已有救援队在前 → × 0.6
        if hotspot.has_rescue_team:
            penalties *= 0.6
            factors["penalty_rescue_team"] = 0.6

        # 道路不可达 → × 0.3
        if not hotspot.road_accessible:
            penalties *= 0.3
            factors["penalty_no_road"] = 0.3

        # 超时 72h → × 0.5
        if hotspot.hours_since_quake > GOLDEN_WINDOW_HOURS:
            penalties *= 0.5
            factors["penalty_timeout"] = 0.5

        factors["total_penalty"] = round(penalties, 3)

        # ---- Step 4: 最终评分 ----
        final_score = base * distress_boost * penalties
        final_score = max(0, min(1, final_score))  # clamp 0-1

        # ---- Step 5: 优先级等级 ----
        if final_score >= 0.8:
            level = "P0"
        elif final_score >= 0.5:
            level = "P1"
        elif final_score >= 0.3:
            level = "P2"
        else:
            level = "P3"

        factors["final_score"] = round(final_score, 3)

        return {
            "score": round(final_score, 3),
            "level": level,
            "factors": factors,
        }

    @staticmethod
    def refresh_all(db: Session, generate_reasons: bool = True) -> int:
        """
        刷新所有热点的优先级
        返回更新数量
        """
        hotspots = db.query(DisasterHotspot).all()
        count = 0

        for hotspot in hotspots:
            result = PriorityEngine.calculate_score(hotspot)

            hotspot.priority_score = result["score"]
            hotspot.priority_level = result["level"]
            hotspot.priority_factors = result["factors"]

            # AI 生成排序理由（可选，避免大量调用）
            if generate_reasons and result["level"] in ("P0", "P1"):
                reason = ai_client.explain_priority({
                    "location": hotspot.location_name,
                    "priority": result["level"],
                    "post_count": hotspot.post_count,
                    "distress_count": hotspot.distress_count,
                    "max_severity": hotspot.max_severity,
                    "estimated_trapped": hotspot.estimated_trapped,
                    "road_accessible": hotspot.road_accessible,
                    "hours_since_quake": hotspot.hours_since_quake,
                    "damage_types": hotspot.damage_types,
                })
                hotspot.priority_reason = reason

            count += 1

        db.commit()
        return count

    @staticmethod
    def get_ranking(db: Session, top_n: Optional[int] = None) -> list:
        """获取优先级排序"""
        query = db.query(DisasterHotspot).order_by(
            desc(DisasterHotspot.priority_score)
        )
        if top_n:
            query = query.limit(top_n)

        hotspots = query.all()
        return [{
            "hotspot_id": h.id,
            "location_name": h.location_name,
            "longitude": h.longitude,
            "latitude": h.latitude,
            "priority_level": h.priority_level or "P3",
            "priority_score": h.priority_score or 0,
            "priority_reason": h.priority_reason,
            "urgency_score": h.urgency_score,
            "post_count": h.post_count,
            "distress_count": h.distress_count,
            "estimated_trapped": h.estimated_trapped,
            "has_rescue_team": h.has_rescue_team,
            "road_accessible": h.road_accessible,
            "factors": h.priority_factors,
        } for h in hotspots]


priority_engine = PriorityEngine()
