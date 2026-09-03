"""AI建筑损毁识别服务 - 当前使用模拟数据"""
import random
from datetime import datetime


def analyze_building_damage(image_url: str = None, disaster_data: dict = None) -> dict:
    """模拟AI建筑损毁分析"""
    damage_levels = ["轻微", "中度", "严重", "完全倒塌"]
    risk_stars = random.randint(1, 5)

    return {
        "damage_level": random.choice(damage_levels),
        "damage_percentage": random.randint(10, 95),
        "building_risk_score": random.randint(20, 100),
        "personnel_risk_stars": risk_stars,
        "suggested_action": get_action(risk_stars),
        "detected_features": random.sample(
            ["墙体裂缝", "结构倾斜", "屋顶坍塌", "窗户破损", "地基下沉", "道路阻断"],
            k=random.randint(2, 4),
        ),
        "confidence": round(random.uniform(0.7, 0.99), 2),
        "analysis_time": datetime.utcnow().isoformat(),
        "model_version": "v1.0-simulated",
    }


def get_action(risk_stars: int) -> str:
    actions = {
        1: "持续监测",
        2: "加强巡查",
        3: "部分疏散",
        4: "全面疏散",
        5: "立即搜救",
    }
    return actions.get(risk_stars, "持续监测")
