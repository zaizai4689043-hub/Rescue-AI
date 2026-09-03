"""
微博数据管道服务
对应愿景 2：实时数据管道

功能：
1. 数据采集 — 企业微博 API 监测关键词（预留接口）
2. 噪声过滤 — 4 层过滤（去重/辟谣/机器人/地理围栏）
3. 数据入库 — 写入 weibo_posts 表
4. 批量导入 — 从 Excel/JSON 导入历史数据
"""
import json
import hashlib
import math
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from models.weibo_post import WeiboPost
from services.nlp_service import nlp_service


# ---- 噪声过滤规则 ----
EARTHQUAKE_KEYWORDS = [
    "地震", "摇晃", "塌了", "被困", "失联", "救援", "物资",
    "伤亡", "遇难", "倒塌", "废墟", "震感", "疏散", "堰塞湖",
    "滑坡", "道路中断", "桥断", "急救", "献血", "帐篷",
]

# 辟谣关键词
RUMOR_KEYWORDS = ["辟谣", "谣言", "不实", "假消息", "澄清"]

# 机器人特征
BOT_THRESHOLD = {
    "max_hashtags": 5,       # 话题标签数
    "min_text_length": 5,    # 最短正文长度
    "max_duplicate_ratio": 0.85,  # 重复率阈值
}


class WeiboPipeline:
    """微博数据管道"""

    @staticmethod
    def generate_post_id(raw_text: str, published_at: str) -> str:
        """生成匿名哈希 ID（不可逆）"""
        raw = f"{raw_text}:{published_at}"
        return "wb-" + hashlib.sha1(raw.encode()).hexdigest()[:16]

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """清洗微博正文"""
        import re
        text = raw_text

        # 去除 URL
        text = re.sub(r'https?://\S+', '', text)
        # 去除 @提及
        text = re.sub(r'@[\w\u4e00-\u9fff]+', '', text)
        # 去除零宽字符
        text = text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
        # 保留最多 1 个话题标签
        tags = re.findall(r'#[^#]+#', text)
        if len(tags) > 1:
            for tag in tags[1:]:
                text = text.replace(tag, '', 1)
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    @staticmethod
    def is_duplicate(text: str, existing_texts: set, threshold: float = 0.85) -> bool:
        """简单重复检测：完全匹配或高相似度"""
        if text in existing_texts:
            return True

        # 简化版 Jaccard 相似度（按字符 bigram）
        def bigrams(s):
            return set(s[i:i+2] for i in range(len(s)-1))

        text_bg = bigrams(text)
        if not text_bg:
            return False

        for existing in existing_texts:
            if len(existing) < 5:
                continue
            existing_bg = bigrams(existing)
            if not existing_bg:
                continue
            intersection = text_bg & existing_bg
            union = text_bg | existing_bg
            similarity = len(intersection) / len(union) if union else 0
            if similarity > threshold:
                return True

        return False

    @staticmethod
    def is_bot_like(text: str) -> bool:
        """检测机器人特征"""
        hashtag_count = text.count("#")
        if hashtag_count > BOT_THRESHOLD["max_hashtags"]:
            return True
        if len(text) < BOT_THRESHOLD["min_text_length"]:
            return True
        return False

    @staticmethod
    def is_rumor(text: str) -> bool:
        """检测辟谣内容"""
        return any(kw in text for kw in RUMOR_KEYWORDS)

    @staticmethod
    def is_within_geo_fence(locations: list, epicenter: tuple, radius_km: float = 300) -> bool:
        """地理围栏过滤：地名是否在震中 ±radius_km 范围内"""
        if not locations:
            return True  # 无地名信息的不过滤（保留）

        epi_lng, epi_lat = epicenter

        for loc in locations:
            lng = loc.get("longitude", 0)
            lat = loc.get("latitude", 0)
            # Haversine 简化版
            dist = math.sqrt(
                (lng - epi_lng) ** 2 * (math.cos(math.radians(epi_lat)) ** 2) +
                (lat - epi_lat) ** 2
            ) * 111  # 粗略转公里
            if dist <= radius_km:
                return True

        return False

    @staticmethod
    def filter_post(text: str, locations: list, existing_texts: set,
                    epicenter: tuple = (95.94, 22.01)) -> tuple:
        """
        4 层噪声过滤
        返回 (is_filtered: bool, reason: str)
        """
        # Layer 1: 去重
        if WeiboPipeline.is_duplicate(text, existing_texts):
            return (True, "duplicate")

        # Layer 2: 辟谣
        if WeiboPipeline.is_rumor(text):
            return (True, "rumor")

        # Layer 3: 机器人
        if WeiboPipeline.is_bot_like(text):
            return (True, "bot")

        # Layer 4: 地理围栏
        if not WeiboPipeline.is_within_geo_fence(locations, epicenter):
            return (True, "geo_out")

        return (False, "")

    @staticmethod
    def ingest_post(db: Session, raw_text: str, published_at: datetime,
                    epicenter: tuple = (95.94, 22.01),
                    user_verified: bool = False,
                    offset_min: Optional[float] = None) -> dict:
        """
        完整处理一条微博：清洗 → 过滤 → NLP → 入库
        返回处理结果
        """
        # 生成 post_id
        time_str = published_at.isoformat()
        post_id = WeiboPipeline.generate_post_id(raw_text, time_str)

        # 检查是否已存在
        existing = db.query(WeiboPost).filter(WeiboPost.post_id == post_id).first()
        if existing:
            return {"status": "exists", "post_id": post_id}

        # 清洗
        cleaned_text = WeiboPipeline.clean_text(raw_text)

        # 灾情关键词初筛
        has_keyword = any(kw in cleaned_text for kw in EARTHQUAKE_KEYWORDS)
        if not has_keyword:
            return {"status": "no_keyword", "post_id": post_id}

        # 获取已有文本用于去重
        recent_posts = db.query(WeiboPost.text).filter(
            WeiboPost.is_filtered == False
        ).limit(1000).all()
        existing_texts = {p.text for p in recent_posts}

        # NLP 预处理（先提取地名用于地理围栏）
        nlp_result = nlp_service.process_post(cleaned_text, user_verified)

        # 4 层过滤
        is_filtered, filter_reason = WeiboPipeline.filter_post(
            cleaned_text, nlp_result["ner_locations"], existing_texts, epicenter
        )

        # 入库
        post = WeiboPost(
            post_id=post_id,
            text=cleaned_text,
            raw_text=raw_text,
            published_at=published_at,
            offset_min=offset_min,
            ner_locations=nlp_result["ner_locations"],
            sentiment=nlp_result["sentiment"],
            damage_type=nlp_result["damage_type"],
            keywords=nlp_result["keywords_matched"],
            severity_vote=nlp_result["severity_vote"],
            credibility=nlp_result["credibility"],
            has_distress_signal=nlp_result["has_distress_signal"],
            distress_keywords=nlp_result["distress_keywords"],
            user_verified=user_verified,
            is_filtered=is_filtered,
            filter_reason=filter_reason if is_filtered else None,
            processed=True,
            processed_at=datetime.now(),
        )
        db.add(post)
        db.commit()

        return {
            "status": "filtered" if is_filtered else "ingested",
            "post_id": post_id,
            "filter_reason": filter_reason if is_filtered else None,
            "nlp": nlp_result if not is_filtered else None,
        }

    @staticmethod
    def batch_ingest(db: Session, posts: list, epicenter: tuple = (95.94, 22.01)) -> dict:
        """批量导入"""
        results = {"ingested": 0, "filtered": 0, "exists": 0, "no_keyword": 0, "errors": 0}

        for post_data in posts:
            try:
                result = WeiboPipeline.ingest_post(
                    db,
                    raw_text=post_data.get("text", ""),
                    published_at=post_data.get("published_at"),
                    epicenter=epicenter,
                    user_verified=post_data.get("user_verified", False),
                    offset_min=post_data.get("offset_min"),
                )
                status = result["status"]
                if status in results:
                    results[status] += 1
            except Exception:
                results["errors"] += 1

        return results

    @staticmethod
    def get_funnel_stats(db: Session) -> dict:
        """数据漏斗统计"""
        total = db.query(func.count(WeiboPost.id)).scalar() or 0
        filtered = db.query(func.count(WeiboPost.id)).filter(
            WeiboPost.is_filtered == True
        ).scalar() or 0
        active = total - filtered

        # 按类型统计
        by_type = db.query(
            WeiboPost.damage_type, func.count(WeiboPost.id)
        ).filter(WeiboPost.is_filtered == False).group_by(WeiboPost.damage_type).all()

        # 按情感统计
        by_sentiment = db.query(
            WeiboPost.sentiment, func.count(WeiboPost.id)
        ).filter(WeiboPost.is_filtered == False).group_by(WeiboPost.sentiment).all()

        # 呼救信号数
        distress_count = db.query(func.count(WeiboPost.id)).filter(
            WeiboPost.has_distress_signal == True,
            WeiboPost.is_filtered == False
        ).scalar() or 0

        return {
            "total": total,
            "filtered": filtered,
            "active": active,
            "by_damage_type": {k: v for k, v in by_type},
            "by_sentiment": {k: v for k, v in by_sentiment},
            "distress_signals": distress_count,
        }


weibo_pipeline = WeiboPipeline()
