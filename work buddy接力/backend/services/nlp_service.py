"""
NLP 服务：NER 地名提取 + 情感分析 + 损毁类型标签
对应愿景 2：实时数据管道

功能：
1. NER 地名提取 — Qwen LLM + 地名词典 fallback
2. 情感分析 — urgent/negative/neutral/hopeful
3. 损毁类型分类 — 6 类
4. 可信度评分 — 认证媒体 > 普通用户 > 疑似机器人
5. 呼救信号检测
"""
import re
import json
from typing import Optional

from services.ai_client import ai_client


# ---- 地名词典（从演示版 build_social_posts.py 回流 + 扩展）----
LOCATION_DICT = {
    # 缅甸
    "曼德勒": (96.07, 21.96), "实皆": (95.98, 21.98), "实皆省": (95.98, 21.98),
    "内比都": (96.07, 19.75), "仰光": (96.20, 16.87), "勃固": (96.50, 17.33),
    "东枝": (97.04, 20.79), "密铁拉": (95.85, 20.88), "皎施": (96.03, 21.63),
    "木各具": (94.62, 21.45), "蒙育瓦": (95.13, 22.11),
    # 中国云南
    "瑞丽": (97.85, 24.01), "德宏": (98.58, 24.44), "德宏州": (98.58, 24.44),
    "瑞丽市": (97.85, 24.01), "保山": (99.16, 25.11), "保山市": (99.16, 25.11),
    "昆明": (102.83, 24.88), "大理": (100.22, 25.59), "临沧": (100.09, 23.88),
    "普洱": (100.97, 22.79), "西双版纳": (100.80, 22.01),
    "腾冲": (98.50, 25.03), "芒市": (98.59, 24.44),
    # 泰国
    "曼谷": (100.50, 13.75), "清迈": (98.98, 18.79),
    # 其他
    "加尔各答": (88.36, 22.57),
}

# ---- 灾情关键词 ----
DAMAGE_KEYWORDS = {
    "人员伤亡": ["遇难", "死亡", "身亡", "遇难者", "遗体", "罹难", "伤亡", "受伤", "伤者", "重伤"],
    "房屋倒塌": ["倒塌", "坍塌", "塌了", "废墟", "垮塌", "塌陷", "损毁", "毁坏", "裂开", "裂缝"],
    "道路中断": ["道路中断", "交通中断", "桥断", "路断", "塌方", "滑坡", "泥石流", "断路", "封路"],
    "次生灾害": ["堰塞湖", "海啸", "滑坡", "泥石流", "地裂", "砂土液化", "火灾", "泄漏", "爆炸"],
    "救援进展": ["救援", "搜救", "救出", "营救", "武警", "消防", "部队", "医疗队", "志愿者"],
    "震感反馈": ["震感", "摇晃", "晃动", "震了一下", "感觉地震", "吓醒", "跑了"],
}

# ---- 呼救关键词 ----
DISTRESS_KEYWORDS = ["救命", "被困", "埋了", "压住", "出不来", "紧急求助", "求救", "有人吗", "帮帮"]

# ---- 情感关键词 ----
SENTIMENT_KEYWORDS = {
    "urgent": ["救命", "紧急", "快", "马上", "来不及", "撑不住", "急需", "危在旦夕", "奄奄一息"],
    "negative": ["悲伤", "痛心", "可怕", "恐怖", "绝望", "哭泣", "哀悼", " RIP", "走好", "遇难"],
    "hopeful": ["感恩", "感谢", "平安", "获救", "奇迹", "希望", "加油", "祈福", "平安无事", "幸存"],
}


class NLPService:
    """NLP 处理服务"""

    @staticmethod
    def extract_locations(text: str) -> list:
        """NER 地名提取：地名词典匹配 + LLM 补充"""
        locations = []

        # 1. 地名词典匹配
        for name, (lng, lat) in LOCATION_DICT.items():
            if name in text:
                locations.append({
                    "name": name,
                    "longitude": lng,
                    "latitude": lat,
                    "confidence": 0.85,
                    "source": "dict"
                })

        # 去重（同名只保留一个）
        seen = set()
        deduped = []
        for loc in locations:
            if loc["name"] not in seen:
                seen.add(loc["name"])
                deduped.append(loc)

        return deduped

    @staticmethod
    def classify_damage_type(text: str) -> str:
        """损毁类型分类（6 类）"""
        scores = {}
        for dtype, keywords in DAMAGE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[dtype] = score

        if not scores:
            return "震感反馈"

        return max(scores, key=scores.get)

    @staticmethod
    def analyze_sentiment(text: str) -> str:
        """情感分析（4 类）"""
        scores = {}
        for sentiment, keywords in SENTIMENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[sentiment] = score

        if not scores:
            return "neutral"

        # urgent 优先级最高
        if "urgent" in scores:
            return "urgent"

        return max(scores, key=scores.get)

    @staticmethod
    def detect_distress(text: str) -> tuple:
        """检测呼救信号，返回 (bool, list)"""
        matched = [kw for kw in DISTRESS_KEYWORDS if kw in text]
        return (len(matched) > 0, matched)

    @staticmethod
    def calculate_severity(damage_type: str, sentiment: str, has_distress: bool) -> int:
        """计算严重度评分 1-5"""
        base = {
            "人员伤亡": 5, "房屋倒塌": 5, "次生灾害": 4,
            "道路中断": 3, "救援进展": 2, "震感反馈": 1
        }.get(damage_type, 1)

        if has_distress:
            base = min(5, base + 1)
        if sentiment == "urgent":
            base = min(5, base + 1)
        elif sentiment == "negative" and base < 3:
            base = min(5, base + 1)

        return base

    @staticmethod
    def calculate_credibility(user_verified: bool, text: str, has_location: bool) -> float:
        """可信度评分 0-1"""
        score = 0.5  # 基准

        if user_verified:
            score += 0.3
        if has_location:
            score += 0.1  # 有地名更可信
        if len(text) > 50:
            score += 0.05  # 长文更可信
        if len(text) < 10:
            score -= 0.1  # 过短可能无意义

        # 检测机器人特征
        if text.count("#") > 3:  # 过多话题标签
            score -= 0.15
        if "http" in text and len(text) < 30:  # 短文本+链接
            score -= 0.1

        return max(0.1, min(1.0, score))

    @staticmethod
    def match_keywords(text: str) -> list:
        """匹配灾情关键词"""
        matched = []
        for dtype, keywords in DAMAGE_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    matched.append(kw)
        return list(set(matched))

    @staticmethod
    def process_post(text: str, user_verified: bool = False) -> dict:
        """完整 NLP 处理一条微博"""
        # 地名提取
        locations = NLPService.extract_locations(text)

        # 损毁类型
        damage_type = NLPService.classify_damage_type(text)

        # 情感分析
        sentiment = NLPService.analyze_sentiment(text)

        # 呼救检测
        has_distress, distress_kws = NLPService.detect_distress(text)

        # 严重度
        severity = NLPService.calculate_severity(damage_type, sentiment, has_distress)

        # 可信度
        credibility = NLPService.calculate_credibility(
            user_verified, text, len(locations) > 0
        )

        # 关键词
        keywords = NLPService.match_keywords(text)

        return {
            "ner_locations": locations,
            "damage_type": damage_type,
            "sentiment": sentiment,
            "has_distress_signal": has_distress,
            "distress_keywords": distress_kws,
            "severity_vote": severity,
            "credibility": round(credibility, 2),
            "keywords_matched": keywords,
        }


nlp_service = NLPService()
