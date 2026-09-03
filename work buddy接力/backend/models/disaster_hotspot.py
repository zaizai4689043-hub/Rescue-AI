"""
灾情热点模型
对应愿景 3：地图聚合 + 动态优先级
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class DisasterHotspot(Base):
    """灾情热点（NER 地名聚合）"""
    __tablename__ = "disaster_hotspots"

    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String(100), nullable=False, index=True)  # 地名
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)

    # 聚合统计
    post_count = Column(Integer, default=0)             # 相关微博数
    urgency_score = Column(Float, default=0)            # 紧急度评分 = 频次 × 严重度
    max_severity = Column(Integer, default=0)           # 最高严重度
    avg_severity = Column(Float, default=0)             # 平均严重度
    damage_types = Column(JSON)                         # {"房屋倒塌": 5, "人员伤亡": 3}
    sentiment_dist = Column(JSON)                       # {"urgent": 3, "negative": 2, ...}
    distress_count = Column(Integer, default=0)         # 呼救信号数

    # 优先级
    priority_level = Column(String(10), index=True)    # P0/P1/P2/P3
    priority_score = Column(Float, default=0)           # 综合评分 0-1
    priority_reason = Column(Text)                      # AI 生成的排序理由
    priority_factors = Column(JSON)                     # 各因子明细

    # 救援状态
    has_rescue_team = Column(Boolean, default=False)    # 是否已有救援队在前
    rescue_status = Column(String(20), default="pending")  # pending/en_route/on_site/done
    estimated_trapped = Column(Integer, default=0)      # 预估被困人数
    road_accessible = Column(Boolean, default=True)     # 道路是否可达
    hours_since_quake = Column(Float, default=0)        # 距发震小时数

    # 关联
    disaster_id = Column(Integer, ForeignKey("disasters.id"), nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
