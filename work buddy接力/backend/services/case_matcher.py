"""
历史案例匹配引擎
对应愿景 6：AI 决策助手 + 案例匹配

功能：
1. 10 维加权相似度计算
2. TOP 3 最相似历史案例匹配
3. 案例策略和经验教训提取
"""
import json
import os
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session

from models.rescue_case import RescueCase


# ---- 匹配维度权重 ----
DIMENSION_WEIGHTS = {
    "magnitude": 0.20,          # 震级（高权重）
    "depth_km": 0.10,           # 震源深度
    "terrain": 0.15,            # 地形（高权重）
    "building_type": 0.15,      # 建筑类型（高权重）
    "population_density": 0.08, # 人口密度
    "season": 0.08,             # 季节天气
    "infrastructure": 0.08,     # 基础设施
    "secondary_hazard": 0.06,   # 次生灾害
    "warning_capability": 0.05, # 预警能力
    "occurrence_time": 0.05,    # 发震时段
}


# ---- JSON 知识库路径 ----
CASES_JSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "rescue_cases.json"
)


class CaseMatcher:
    """案例匹配引擎"""

    @staticmethod
    def load_cases_from_json() -> list:
        """从 JSON 文件加载案例"""
        if not os.path.exists(CASES_JSON_PATH):
            return []
        with open(CASES_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def sync_to_database(db: Session) -> int:
        """将 JSON 案例同步到数据库"""
        cases = CaseMatcher.load_cases_from_json()
        count = 0

        for case_data in cases:
            case_id = case_data.get("case_id")
            existing = db.query(RescueCase).filter(
                RescueCase.case_id == case_id
            ).first()

            if existing:
                # 更新
                for key, value in case_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                # 新建
                case = RescueCase(**{
                    k: v for k, v in case_data.items()
                    if hasattr(RescueCase, k) and k != "id"
                })
                db.add(case)

            count += 1

        db.commit()
        return count

    @staticmethod
    def calculate_similarity(query: dict, case: dict) -> tuple:
        """
        计算相似度
        返回 (score, dimension_scores)
        """
        dimension_scores = {}
        total_score = 0

        # 震级相似度（连续值，差值越小越相似）
        q_mag = query.get("magnitude", 0)
        c_mag = case.get("magnitude", 0)
        mag_diff = abs(q_mag - c_mag)
        mag_score = max(0, 1 - mag_diff / 3)  # 差 3 级以上得 0
        dimension_scores["magnitude"] = mag_score
        total_score += mag_score * DIMENSION_WEIGHTS["magnitude"]

        # 震源深度相似度
        q_depth = query.get("depth_km", 10)
        c_depth = case.get("depth_km", 10)
        depth_diff = abs(q_depth - c_depth)
        depth_score = max(0, 1 - depth_diff / 50)  # 差 50km 以上得 0
        dimension_scores["depth_km"] = depth_score
        total_score += depth_score * DIMENSION_WEIGHTS["depth_km"]

        # 地形相似度（精确匹配）
        q_terrain = query.get("terrain", "")
        c_terrain = case.get("terrain", "")
        terrain_score = 1.0 if q_terrain == c_terrain else 0.3
        dimension_scores["terrain"] = terrain_score
        total_score += terrain_score * DIMENSION_WEIGHTS["terrain"]

        # 建筑类型相似度
        q_building = query.get("building_type", "")
        c_building = case.get("building_type", "")
        building_score = 1.0 if q_building == c_building else 0.3
        dimension_scores["building_type"] = building_score
        total_score += building_score * DIMENSION_WEIGHTS["building_type"]

        # 人口密度
        q_pop = query.get("population_density", "")
        c_pop = case.get("population_density", "")
        pop_score = 1.0 if q_pop == c_pop else 0.4
        dimension_scores["population_density"] = pop_score
        total_score += pop_score * DIMENSION_WEIGHTS["population_density"]

        # 季节
        q_season = query.get("season", "")
        c_season = case.get("season", "")
        season_score = 1.0 if q_season == c_season else 0.3
        dimension_scores["season"] = season_score
        total_score += season_score * DIMENSION_WEIGHTS["season"]

        # 基础设施
        q_infra = query.get("infrastructure", "")
        c_infra = case.get("infrastructure", "")
        infra_score = 1.0 if q_infra == c_infra else 0.4
        dimension_scores["infrastructure"] = infra_score
        total_score += infra_score * DIMENSION_WEIGHTS["infrastructure"]

        # 次生灾害
        q_hazard = query.get("secondary_hazard", "")
        c_hazard = case.get("secondary_hazard", "")
        if q_hazard and c_hazard:
            # 检查是否有交集
            q_hazards = set(q_hazard.split(","))
            c_hazards = set(c_hazard.split(","))
            hazard_score = len(q_hazards & c_hazards) / max(len(q_hazards | c_hazards), 1)
        elif not q_hazard and not c_hazard:
            hazard_score = 0.5
        else:
            hazard_score = 0.2
        dimension_scores["secondary_hazard"] = hazard_score
        total_score += hazard_score * DIMENSION_WEIGHTS["secondary_hazard"]

        # 预警能力
        q_warning = query.get("warning_capability", "")
        c_warning = case.get("warning_capability", "")
        warning_score = 1.0 if q_warning == c_warning else 0.3
        dimension_scores["warning_capability"] = warning_score
        total_score += warning_score * DIMENSION_WEIGHTS["warning_capability"]

        # 发震时段
        q_time = query.get("occurrence_time", "")
        c_time = case.get("occurrence_time", "")
        time_score = 1.0 if q_time == c_time else 0.4
        dimension_scores["occurrence_time"] = time_score
        total_score += time_score * DIMENSION_WEIGHTS["occurrence_time"]

        return (round(total_score, 3), dimension_scores)

    @staticmethod
    def match(db: Session, query: dict, top_n: int = 3) -> list:
        """
        匹配最相似的历史案例
        返回 [{case_id, name, magnitude, similarity_score, match_dimensions, strategies, lessons}]
        """
        # 先从数据库查，没有则从 JSON 查
        cases = db.query(RescueCase).all()

        if not cases:
            # 从 JSON 加载
            json_cases = CaseMatcher.load_cases_from_json()
            results = []
            for case_data in json_cases:
                score, dims = CaseMatcher.calculate_similarity(query, case_data)
                results.append((case_data, score, dims))
        else:
            results = []
            for case in cases:
                case_dict = {
                    "magnitude": case.magnitude,
                    "depth_km": case.depth_km,
                    "terrain": case.terrain,
                    "building_type": case.building_type,
                    "population_density": case.population_density,
                    "season": case.season,
                    "infrastructure": case.infrastructure,
                    "secondary_hazard": case.secondary_hazard,
                    "warning_capability": case.warning_capability,
                    "occurrence_time": case.occurrence_time,
                }
                score, dims = CaseMatcher.calculate_similarity(query, case_dict)
                case_data = {
                    "case_id": case.case_id,
                    "name": case.name,
                    "magnitude": case.magnitude,
                    "casualties": case.casualties,
                    "location": case.location,
                    "strategies": case.strategies,
                    "lessons": case.lessons,
                    "tags": case.tags,
                    "timeline": case.timeline,
                }
                results.append((case_data, score, dims))

        # 排序取 TOP N
        results.sort(key=lambda x: x[1], reverse=True)
        top_results = results[:top_n]

        return [{
            "case_id": r[0].get("case_id", ""),
            "name": r[0].get("name", ""),
            "magnitude": r[0].get("magnitude", 0),
            "casualties": r[0].get("casualties", 0),
            "location": r[0].get("location", ""),
            "similarity_score": r[1],
            "match_dimensions": r[2],
            "strategies": r[0].get("strategies", []),
            "lessons": r[0].get("lessons", []),
            "tags": r[0].get("tags", []),
            "timeline": r[0].get("timeline", []),
        } for r in top_results]


case_matcher = CaseMatcher()
