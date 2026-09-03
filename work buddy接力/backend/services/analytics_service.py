"""
多维分析仪表盘服务
对应愿景 4：社媒舆情多维分析

功能：
1. 损毁类型分布图（饼图）
2. 关键词频率排行（柱状图）
3. 时间线情感变化折线图
4. 新兴关键词检测（突然大量出现 → 次生灾害预警）
5. 官方通报时间点叠加
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from models.weibo_post import WeiboPost


class AnalyticsService:
    """多维分析服务"""

    @staticmethod
    def get_damage_type_distribution(db: Session) -> list:
        """损毁类型分布"""
        results = db.query(
            WeiboPost.damage_type,
            func.count(WeiboPost.id).label("count")
        ).filter(
            WeiboPost.is_filtered == False,
            WeiboPost.damage_type.isnot(None)
        ).group_by(WeiboPost.damage_type).all()

        total = sum(r.count for r in results) or 1

        return [{
            "damage_type": r.damage_type,
            "count": r.count,
            "percentage": round(r.count / total * 100, 1)
        } for r in sorted(results, key=lambda x: x.count, reverse=True)]

    @staticmethod
    def get_keyword_frequencies(db: Session, top_n: int = 20) -> list:
        """关键词频率排行"""
        posts = db.query(WeiboPost.keywords).filter(
            WeiboPost.is_filtered == False,
            WeiboPost.keywords.isnot(None)
        ).all()

        counter = Counter()
        for post in posts:
            if post.keywords:
                for kw in post.keywords:
                    counter[kw] += 1

        top_keywords = counter.most_common(top_n)

        return [{
            "keyword": kw,
            "count": cnt,
            "trend": "stable"  # TODO: 与历史对比计算趋势
        } for kw, cnt in top_keywords]

    @staticmethod
    def get_sentiment_timeline(db: Session, interval_minutes: int = 30) -> list:
        """
        时间线情感变化
        按 interval_minutes 分桶统计情感分布
        """
        posts = db.query(WeiboPost).filter(
            WeiboPost.is_filtered == False,
            WeiboPost.published_at.isnot(None)
        ).order_by(WeiboPost.published_at).all()

        if not posts:
            return []

        # 找到时间范围
        start_time = posts[0].published_at
        end_time = posts[-1].published_at

        # 分桶
        timeline = []
        current = start_time
        while current <= end_time:
            bucket_end = current + timedelta(minutes=interval_minutes)
            bucket_posts = [p for p in posts if current <= p.published_at < bucket_end]

            if bucket_posts:
                sentiment_counts = {"urgent": 0, "negative": 0, "neutral": 0, "hopeful": 0}
                for p in bucket_posts:
                    if p.sentiment in sentiment_counts:
                        sentiment_counts[p.sentiment] += 1

                timeline.append({
                    "timestamp": current.strftime("%H:%M"),
                    "urgent": sentiment_counts["urgent"],
                    "negative": sentiment_counts["negative"],
                    "neutral": sentiment_counts["neutral"],
                    "hopeful": sentiment_counts["hopeful"],
                    "total": len(bucket_posts),
                })

            current = bucket_end

        return timeline

    @staticmethod
    def get_top_distress_areas(db: Session, top_n: int = 10) -> list:
        """获取呼救信号最多的区域"""
        posts = db.query(WeiboPost).filter(
            WeiboPost.has_distress_signal == True,
            WeiboPost.is_filtered == False,
            WeiboPost.ner_locations.isnot(None)
        ).all()

        area_counter = Counter()
        for post in posts:
            if post.ner_locations:
                for loc in post.ner_locations:
                    name = loc.get("name", "")
                    if name:
                        area_counter[name] += 1

        return [{"area": area, "distress_count": count}
                for area, count in area_counter.most_common(top_n)]

    @staticmethod
    def detect_emerging_keywords(db: Session, threshold: int = 5) -> list:
        """
        新兴关键词检测
        检测在最近时间段内突然大量出现的关键词（可能是次生灾害前兆）
        """
        posts = db.query(WeiboPost).filter(
            WeiboPost.is_filtered == False,
            WeiboPost.keywords.isnot(None)
        ).order_by(desc(WeiboPost.published_at)).limit(100).all()

        recent_counter = Counter()
        for post in posts[:50]:  # 最近 50 条
            if post.keywords:
                for kw in post.keywords:
                    recent_counter[kw] += 1

        older_counter = Counter()
        for post in posts[50:]:  # 之前 50 条
            if post.keywords:
                for kw in post.keywords:
                    older_counter[kw] += 1

        emerging = []
        for kw, count in recent_counter.items():
            older_count = older_counter.get(kw, 0)
            if count >= threshold and count > older_count * 2:
                emerging.append({
                    "keyword": kw,
                    "recent_count": count,
                    "previous_count": older_count,
                    "increase_ratio": round(count / max(older_count, 1), 1)
                })

        return sorted(emerging, key=lambda x: x["increase_ratio"], reverse=True)

    @staticmethod
    def get_dashboard(db: Session) -> dict:
        """获取完整仪表盘数据"""
        # 汇总统计
        total_posts = db.query(func.count(WeiboPost.id)).filter(
            WeiboPost.is_filtered == False
        ).scalar() or 0

        distress_posts = db.query(func.count(WeiboPost.id)).filter(
            WeiboPost.is_filtered == False,
            WeiboPost.has_distress_signal == True
        ).scalar() or 0

        avg_severity = db.query(func.avg(WeiboPost.severity_vote)).filter(
            WeiboPost.is_filtered == False
        ).scalar() or 0

        avg_credibility = db.query(func.avg(WeiboPost.credibility)).filter(
            WeiboPost.is_filtered == False
        ).scalar() or 0

        return {
            "summary": {
                "total_posts": total_posts,
                "distress_posts": distress_posts,
                "avg_severity": round(float(avg_severity), 2),
                "avg_credibility": round(float(avg_credibility), 2),
            },
            "damage_type_distribution": AnalyticsService.get_damage_type_distribution(db),
            "keyword_frequencies": AnalyticsService.get_keyword_frequencies(db),
            "sentiment_timeline": AnalyticsService.get_sentiment_timeline(db),
            "top_distress_areas": AnalyticsService.get_top_distress_areas(db),
            "emerging_keywords": AnalyticsService.detect_emerging_keywords(db),
        }


analytics_service = AnalyticsService()
