"""
物资运输记录模型
对应无人机空中救援模块 - 物资投送
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class SupplyDelivery(Base):
    """物资投送记录"""
    __tablename__ = "supply_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("drone_missions.id"), nullable=True)
    drone_id_str = Column(String(50), index=True)              # 无人机编号

    # 投送目标
    target_location = Column(String(100), nullable=False)      # 投送地点
    target_lng = Column(Float)
    target_lat = Column(Float)

    # 物资清单
    manifest = Column(JSON, nullable=False)                    # [{"item":"帐篷","qty":5,"weight_kg":2,"category":"shelter"}]
    total_weight_kg = Column(Float, default=0)
    total_items = Column(Integer, default=0)

    # 物资分类统计
    category_summary = Column(JSON)                            # {"shelter":5,"food":10,"medical":3,"water":8}

    # 投送状态
    status = Column(String(20), default="pending", index=True) # pending/loading/en_route/delivered/confirmed/failed
    priority = Column(String(5), default="P1")                 # P0/P1/P2/P3

    # 投送详情
    drop_method = Column(String(30), default="hover_drop")     # hover_drop/land/parachute
    drop_altitude_m = Column(Float, default=5)                 # 投送高度
    drop_accuracy_m = Column(Float)                            # 投送精度（偏差米数）

    # 时间线
    requested_at = Column(DateTime, default=func.now())
    loaded_at = Column(DateTime)
    departed_at = Column(DateTime)
    delivered_at = Column(DateTime)
    confirmed_at = Column(DateTime)

    # 受领确认
    received_by = Column(String(100))                          # 受领人/单位
    received_count = Column(Integer)                           # 实收数量
    shortage_count = Column(Integer, default=0)                # 短缺数量
    confirmation_note = Column(Text)                           # 受领备注

    # 失败记录
    fail_reason = Column(String(200))
    retry_count = Column(Integer, default=0)

    # 关联灾情
    disaster_id = Column(Integer, ForeignKey("disasters.id"), nullable=True)
    hotspot_id = Column(Integer, ForeignKey("disaster_hotspots.id"), nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
