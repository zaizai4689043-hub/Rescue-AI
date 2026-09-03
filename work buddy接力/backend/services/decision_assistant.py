"""
AI 决策助手
对应愿景 6：智能预测 + 案例匹配 + 行动方案

功能：
1. 基于微博数据智能预测"最需要优先救援"的地区
2. 附带数据依据（频次、严重度、呼救信号、可信度）
3. 匹配过往救援案例，给出参考策略
4. Qwen3.8-Max 生成综合行动方案
5. 风险预警和资源调配建议
"""
import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from models.weibo_post import WeiboPost
from models.disaster_hotspot import DisasterHotspot
from services.ai_client import ai_client
from services.case_matcher import case_matcher
from services.analytics_service import analytics_service
from services.priority_engine import priority_engine


class DecisionAssistant:
    """AI 决策助手"""

    @staticmethod
    def collect_situation(db: Session, epicenter: tuple = (95.94, 22.01),
                          magnitude: float = 7.7, depth_km: float = 10.0) -> dict:
        """收集当前灾情态势快照"""
        # 优先级排序
        ranking = priority_engine.get_ranking(db, top_n=10)

        # 分析仪表盘
        dashboard = analytics_service.get_dashboard(db)

        # 新兴关键词（次生灾害预警）
        emerging = analytics_service.detect_emerging_keywords(db)

        # 呼救区域
        distress_areas = analytics_service.get_top_distress_areas(db)

        return {
            "epicenter": {"lng": epicenter[0], "lat": epicenter[1]},
            "magnitude": magnitude,
            "depth_km": depth_km,
            "priority_ranking": ranking,
            "analytics_summary": dashboard["summary"],
            "top_distress_areas": distress_areas,
            "emerging_keywords": emerging,
            "damage_type_distribution": dashboard["damage_type_distribution"],
            "sentiment_timeline_tail": dashboard["sentiment_timeline"][-5:] if dashboard["sentiment_timeline"] else [],
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def analyze(db: Session, epicenter: tuple = (95.94, 22.01),
                magnitude: float = 7.7, depth_km: float = 10.0) -> dict:
        """
        AI 决策分析
        返回完整决策建议
        """
        # 1. 收集态势
        situation = DecisionAssistant.collect_situation(
            db, epicenter, magnitude, depth_km
        )

        # 2. 案例匹配
        # 推断匹配维度
        # 根据震级和震源深度推断地形等维度（简化版）
        query = DecisionAssistant._infer_match_query(magnitude, depth_km, situation)
        matched_cases = case_matcher.match(db, query, top_n=3)

        # 3. AI 综合研判
        ai_result = ai_client.generate_decision(situation, matched_cases)

        if ai_result:
            return {
                "priority_areas": ai_result.get("priority_areas", []),
                "action_plan": ai_result.get("action_plan", ""),
                "matched_cases": matched_cases,
                "risk_warnings": ai_result.get("risk_warnings", []),
                "resource_suggestions": ai_result.get("resource_suggestions", []),
                "reference_case": ai_result.get("reference_case", ""),
                "situation_snapshot": situation,
                "ai_powered": True,
            }
        else:
            # 降级：基于规则生成
            return DecisionAssistant._fallback_decision(situation, matched_cases)

    @staticmethod
    def _infer_match_query(magnitude: float, depth_km: float, situation: dict) -> dict:
        """根据当前态势推断案例匹配维度"""
        # 根据震源深度判断地形倾向
        if depth_km < 15:
            terrain = "山区"  # 浅源多见于山区
        elif depth_km < 30:
            terrain = "高原"
        else:
            terrain = "平原"

        # 根据震级判断建筑类型倾向
        if magnitude >= 7.5:
            building_type = "混合"  # 大震影响范围广
        else:
            building_type = "砖混"

        # 季节（当前月份）
        month = datetime.now().month
        if 3 <= month <= 5:
            season = "春"
        elif 6 <= month <= 8:
            season = "夏"
        elif 9 <= month <= 11:
            season = "秋"
        else:
            season = "冬"

        # 从新兴关键词推断次生灾害
        emerging = situation.get("emerging_keywords", [])
        hazard_keywords = ["堰塞湖", "滑坡", "泥石流", "海啸", "火灾", "泄漏"]
        detected_hazards = [k["keyword"] for k in emerging if k["keyword"] in hazard_keywords]
        secondary_hazard = ",".join(detected_hazards) if detected_hazards else ""

        return {
            "magnitude": magnitude,
            "depth_km": depth_km,
            "terrain": terrain,
            "building_type": building_type,
            "population_density": "中",
            "season": season,
            "infrastructure": "一般",
            "secondary_hazard": secondary_hazard,
            "warning_capability": "有",
            "occurrence_time": "午间",
        }

    @staticmethod
    def _fallback_decision(situation: dict, matched_cases: list) -> dict:
        """降级决策（AI 不可用时基于规则）"""
        ranking = situation.get("priority_ranking", [])

        # 取优先级最高的区域
        priority_areas = []
        for item in ranking[:5]:
            if item.get("priority_level") in ("P0", "P1"):
                priority_areas.append({
                    "name": item["location_name"],
                    "reason": f"优先级{item['priority_level']}，"
                              f"相关帖文{item['post_count']}条，"
                              f"呼救信号{item['distress_count']}条，"
                              f"预估被困{item['estimated_trapped']}人",
                    "score": item["priority_score"],
                    "estimated_trapped": item["estimated_trapped"],
                })

        # 风险预警
        risk_warnings = []
        emerging = situation.get("emerging_keywords", [])
        for item in emerging[:3]:
            risk_warnings.append(
                f"关键词「{item['keyword']}」近期出现频率激增"
                f"（增长{item['increase_ratio']}倍），"
                f"请关注潜在次生灾害风险"
            )

        # 资源建议
        resource_suggestions = []
        damage_dist = situation.get("damage_type_distribution", [])
        for item in damage_dist[:3]:
            dtype = item["damage_type"]
            if dtype == "房屋倒塌":
                resource_suggestions.append("增调搜救犬、生命探测仪、破拆设备")
            elif dtype == "人员伤亡":
                resource_suggestions.append("增调医疗队、急救物资、血浆")
            elif dtype == "道路中断":
                resource_suggestions.append("调度工程机械、开辟直升机通道")

        # 行动方案
        top_area = priority_areas[0]["name"] if priority_areas else "震中周边"
        ref_case = matched_cases[0]["name"] if matched_cases else "历史案例"

        action_plan = (
            f"建议优先派遣救援力量前往{top_area}。"
            f"参考{ref_case}的救援经验，"
            f"按黄金72小时原则展开搜索。"
            f"同步部署无人机侦察和通信保障。"
        )

        return {
            "priority_areas": priority_areas,
            "action_plan": action_plan,
            "matched_cases": matched_cases,
            "risk_warnings": risk_warnings,
            "resource_suggestions": resource_suggestions,
            "reference_case": matched_cases[0]["case_id"] if matched_cases else None,
            "situation_snapshot": situation,
            "ai_powered": False,
        }


decision_assistant = DecisionAssistant()
