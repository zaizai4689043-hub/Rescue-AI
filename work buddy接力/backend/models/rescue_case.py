"""
救援案例知识库模型
对应愿景 6：AI 决策助手 + 案例匹配
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Float, JSON
from sqlalchemy.sql import func

from app.database import Base


class RescueCase(Base):
    """历史地震救援案例"""
    __tablename__ = "rescue_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(20), unique=True, nullable=False)  # C-01 ~ C-08
    name = Column(String(100), nullable=False)

    # 震情参数
    magnitude = Column(Float, nullable=False)
    depth_km = Column(Float)
    location = Column(String(200))
    latitude = Column(Float)
    longitude = Column(Float)
    occurred_at = Column(Date)
    casualties = Column(Integer)                        # 遇难/失踪人数
    affected_population = Column(Integer)               # 受灾人口

    # 匹配维度（10 维）
    terrain = Column(String(50))                        # 地形：山区/高原/平原/沿海
    building_type = Column(String(50))                  # 建筑类型：砖混/框架/土石/混合
    population_density = Column(String(50))             # 人口密度：高/中/低
    season = Column(String(20))                         # 春/夏/秋/冬
    weather = Column(Text)                              # 天气条件
    infrastructure = Column(String(50))                 # 基础设施：发达/一般/薄弱
    secondary_hazard = Column(Text)                     # 次生灾害类型
    warning_capability = Column(String(50))             # 预警能力：有/无
    occurrence_time = Column(String(50))                # 发震时段：晨间/午间/夜间

    # 救援信息
    timeline = Column(JSON)                             # [{time, event, description}]
    strategies = Column(JSON)                           # [{strategy, description}]
    lessons = Column(JSON)                              # [str]
    tags = Column(JSON)                                 # [str]

    created_at = Column(DateTime, default=func.now())
