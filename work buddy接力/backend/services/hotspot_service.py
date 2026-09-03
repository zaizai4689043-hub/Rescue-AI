"""
灾情热点聚合服务
对应愿景 3：地图聚合

功能：
1. 将微博 NER 地名聚合到地图上
2. 按出现频次和严重程度加权生成灾情热力图
3. 呼救信号 + 地点定位 → 热点加权
"""
from collections import defaultdict
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from models.weibo_post import WeiboPost
from models.disaster_hotspot import DisasterHotspot


class HotspotService:
    """灾情热点聚合"""

    @staticmethod
    def rebuild_hotspots(db: Session, quake_time: Optional[datetime] = None) -> int:
        """
        从微博数据重建灾情热点
        返回生成的热点数量
        """
        if quake_time is None:
            quake_time = datetime(2025, 3, 28, 14, 20, 52)  # 缅甸地震默认时间

        # 查询所有未过滤且有地名信息的微博
        posts = db.query(WeiboPost).filter(
            WeiboPost.is_filtered == False,
            WeiboPost.ner_locations.isnot(None)
        ).all()

        # 按地名聚合
        hotspot_map = defaultdict(lambda: {
            "posts": [],
            "longitude": 0,
            "latitude": 0,
            "count": 0,
        })

        for post in posts:
            if not post.ner_locations:
                continue
            for loc in post.ner_locations:
                name = loc.get("name", "")
                if not name:
                    continue

                hotspot_map[name]["posts"].append(post)
                hotspot_map[name]["longitude"] = loc.get("longitude", 0)
                hotspot_map[name]["latitude"] = loc.get("latitude", 0)
                hotspot_map[name]["count"] += 1

        # 清空旧热点
        db.query(DisasterHotspot).delete()

        # 生成新热点
        count = 0
        now = datetime.now()
        hours_since = (now - quake_time).total_seconds() / 3600 if now > quake_time else 0

        for name, data in hotspot_map.items():
            posts = data["posts"]
            post_count = len(posts)

            if post_count == 0:
                continue

            # 统计
            severities = [p.severity_vote for p in posts]
            max_severity = max(severities)
            avg_severity = sum(severities) / len(severities)

            # 损毁类型分布
            damage_types = defaultdict(int)
            for p in posts:
                if p.damage_type:
                    damage_types[p.damage_type] += 1

            # 情感分布
            sentiment_dist = defaultdict(int)
            for p in posts:
                if p.sentiment:
                    sentiment_dist[p.sentiment] += 1

            # 呼救信号数
            distress_count = sum(1 for p in posts if p.has_distress_signal)

            # 紧急度评分 = 频次 × 平均严重度 × 可信度加权
            avg_credibility = sum(p.credibility for p in posts) / post_count
            urgency_score = post_count * avg_severity * avg_credibility

            # 预估被困人数（粗略：呼救数 × 5 + 严重度 > 4 的帖数 × 3）
            estimated_trapped = distress_count * 5 + sum(1 for s in severities if s >= 4) * 3

            hotspot = DisasterHotspot(
                location_name=name,
                longitude=data["longitude"],
                latitude=data["latitude"],
                post_count=post_count,
                urgency_score=round(urgency_score, 2),
                max_severity=max_severity,
                avg_severity=round(avg_severity, 2),
                damage_types=dict(damage_types),
                sentiment_dist=dict(sentiment_dist),
                distress_count=distress_count,
                estimated_trapped=estimated_trapped,
                hours_since_quake=round(hours_since, 1),
                road_accessible=True,  # 默认可达，后续可通过道路中断标记更新
            )
            db.add(hotspot)
            count += 1

        db.commit()
        return count

    @staticmethod
    def get_hotspots(db: Session, min_posts: int = 1) -> list:
        """获取灾情热点列表"""
        return db.query(DisasterHotspot).filter(
            DisasterHotspot.post_count >= min_posts
        ).order_by(desc(DisasterHotspot.urgency_score)).all()

    @staticmethod
    def get_heatmap_data(db: Session) -> list:
        """获取热力图数据（ECharts 格式）"""
        hotspots = db.query(DisasterHotspot).filter(
            DisasterHotspot.post_count >= 1
        ).all()

        return [{
            "name": h.location_name,
            "value": [h.longitude, h.latitude, h.urgency_score],
            "post_count": h.post_count,
            "max_severity": h.max_severity,
            "priority_level": h.priority_level,
            "distress_count": h.distress_count,
        } for h in hotspots]

    @staticmethod
    def update_rescue_status(db: Session, hotspot_id: int, status: str,
                             has_team: bool = True) -> bool:
        """更新救援状态"""
        hotspot = db.query(DisasterHotspot).filter(
            DisasterHotspot.id == hotspot_id
        ).first()
        if not hotspot:
            return False

        hotspot.rescue_status = status
        hotspot.has_rescue_team = has_team
        db.commit()
        return True

    @staticmethod
    def update_road_access(db: Session, hotspot_id: int, accessible: bool) -> bool:
        """更新道路可达性"""
        hotspot = db.query(DisasterHotspot).filter(
            DisasterHotspot.id == hotspot_id
        ).first()
        if not hotspot:
            return False

        hotspot.road_accessible = accessible
        db.commit()
        return True


hotspot_service = HotspotService()
