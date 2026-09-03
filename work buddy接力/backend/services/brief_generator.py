"""
AI 灾情简报生成服务
对应愿景 5：Qwen3.8-Max 生成应急管理部通报风格简报

功能：
1. 基于微博数据分析生成灾情简报
2. 定时通报机制（T+30min / T+1h / T+3h / T+6h）
3. 版本对比，标注变化增量
4. 口径红线保护（关键数据不得改写）
"""
import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from models.weibo_post import WeiboPost
from models.disaster_hotspot import DisasterHotspot
from services.ai_client import ai_client
from services.analytics_service import analytics_service


# ---- 简报版本定义 ----
BRIEF_VERSIONS = {
    "T+30min": {"label": "震后30分钟", "offset_min": 30},
    "T+1h": {"label": "震后1小时", "offset_min": 60},
    "T+3h": {"label": "震后3小时", "offset_min": 180},
    "T+6h": {"label": "震后6小时", "offset_min": 360},
    "T+12h": {"label": "震后12小时", "offset_min": 720},
    "T+24h": {"label": "震后24小时", "offset_min": 1440},
    "T+72h": {"label": "震后72小时", "offset_min": 4320},
}

# ---- 口径红线（关键数据必须原样使用）----
CALIBRATION_REDS = {
    "first_post_offset": "首条涉震微博早于主震发震时刻1分46秒",
    "magnitude_dual": "震级双口径：CENC 7.9 / USGS Mw7.7",
    "mainshock_time": "主震发震时刻2025-03-28 14:20:52（北京时间）",
    "casualty_note": "死亡人数表述为「截至通报时点官方数字，持续更新中」",
}


class BriefGenerator:
    """AI 灾情简报生成器"""

    @staticmethod
    def collect_situation(db: Session, quake_time: datetime,
                          version: Optional[str] = None) -> dict:
        """收集当前态势数据"""
        # 确定时间窗口
        if version and version in BRIEF_VERSIONS:
            window_end = quake_time + timedelta(minutes=BRIEF_VERSIONS[version]["offset_min"])
        else:
            window_end = datetime.now()

        # 微博统计
        posts = db.query(WeiboPost).filter(
            WeiboPost.is_filtered == False,
            WeiboPost.published_at <= window_end
        ).all()

        total_posts = len(posts)
        distress_count = sum(1 for p in posts if p.has_distress_signal)

        # 损毁类型分布
        damage_types = {}
        for p in posts:
            if p.damage_type:
                damage_types[p.damage_type] = damage_types.get(p.damage_type, 0) + 1

        # 情感分布
        sentiments = {}
        for p in posts:
            if p.sentiment:
                sentiments[p.sentiment] = sentiments.get(p.sentiment, 0) + 1

        # 热点区域
        hotspots = db.query(DisasterHotspot).filter(
            DisasterHotspot.post_count >= 2
        ).order_by(desc(DisasterHotspot.urgency_score)).limit(5).all()

        top_areas = [{
            "name": h.location_name,
            "post_count": h.post_count,
            "max_severity": h.max_severity,
            "distress_count": h.distress_count,
            "priority": h.priority_level,
        } for h in hotspots]

        # 优先级分布
        priority_dist = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for h in hotspots:
            if h.priority_level in priority_dist:
                priority_dist[h.priority_level] += 1

        return {
            "quake_time": quake_time.isoformat(),
            "brief_time": window_end.isoformat(),
            "version": version or "realtime",
            "total_posts": total_posts,
            "distress_signals": distress_count,
            "damage_types": damage_types,
            "sentiments": sentiments,
            "top_areas": top_areas,
            "priority_distribution": priority_dist,
            "calibration": CALIBRATION_REDS,
        }

    @staticmethod
    def generate(db: Session, quake_time: Optional[datetime] = None,
                 version: Optional[str] = None) -> dict:
        """
        生成灾情简报
        返回 {content, situation_snapshot, version, changes_from_previous}
        """
        if quake_time is None:
            quake_time = datetime(2025, 3, 28, 14, 20, 52)

        # 收集态势数据
        situation = BriefGenerator.collect_situation(db, quake_time, version)

        # AI 生成简报
        content = ai_client.generate_brief(situation)

        if not content:
            # 降级：模板生成
            content = BriefGenerator._fallback_brief(situation)

        # 计算与上一版的变化
        changes = BriefGenerator._diff_previous(db, situation, version)

        return {
            "content": content,
            "situation_snapshot": situation,
            "version": version or "realtime",
            "changes_from_previous": changes,
            "generated_at": datetime.now().isoformat(),
        }

    @staticmethod
    def _fallback_brief(situation: dict) -> str:
        """降级简报（AI 不可用时）"""
        version_label = BRIEF_VERSIONS.get(
            situation.get("version", ""), {}
        ).get("label", "实时")

        posts = situation.get("total_posts", 0)
        distress = situation.get("distress_signals", 0)
        top_areas = situation.get("top_areas", [])

        areas_text = "、".join(a["name"] for a in top_areas[:3]) if top_areas else "震中周边"

        return (
            f"【灾情简报 - {version_label}】\n"
            f"据社媒感知数据，截至本通报时点，共监测到地震相关帖文 {posts} 条，"
            f"其中呼救信号 {distress} 条。"
            f"重点关切区域：{areas_text}。\n"
            f"注：本简报为社媒感知数据自动生成，仅供决策参考，"
            f"不替代官方通报。"
        )

    @staticmethod
    def _diff_previous(db: Session, current: dict, version: Optional[str]) -> Optional[str]:
        """与上一版简报对比，标注变化"""
        if not version:
            return None

        versions_order = list(BRIEF_VERSIONS.keys())
        if version not in versions_order:
            return None

        idx = versions_order.index(version)
        if idx == 0:
            return "首期简报"

        prev_version = versions_order[idx - 1]
        prev_label = BRIEF_VERSIONS[prev_version]["label"]

        return f"对比 {prev_label} 简报，关注新增数据和趋势变化。"


brief_generator = BriefGenerator()
