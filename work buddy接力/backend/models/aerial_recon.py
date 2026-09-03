"""
空中侦察记录模型
对应无人机空中救援模块 - 灾情侦察 / 路线研判
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class AerialRecon(Base):
    """空中侦察记录"""
    __tablename__ = "aerial_recons"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("drone_missions.id"), nullable=True)
    drone_id_str = Column(String(50), index=True)              # 无人机编号

    # 侦察区域
    area_name = Column(String(100), nullable=False)            # 侦察区域名称
    center_lng = Column(Float)
    center_lat = Column(Float)
    coverage_sqkm = Column(Float, default=0)                   # 覆盖面积 km^2

    # 采集素材
    images = Column(JSON)                                      # [{"url","taken_at","lng","lat","alt","heading","note"}]
    videos = Column(JSON)                                      # [{"url","duration_s","taken_at","lng","lat"}]
    thermal_images = Column(JSON)                              # 热成像图片
    lidar_point_count = Column(Integer, default=0)             # 激光点云点数

    # AI 路线分析
    route_analysis = Column(Text)                              # AI 生成的路线分析文本
    route_assessment = Column(JSON)  # 结构化路线研判
    """
    route_assessment 结构：
    {
        "accessible_routes": [
            {"from":"指挥部","to":"实皆村","via":"北线公路","status":"clear","estimated_time_min":45,"notes":"路面完好"}
        ],
        "blocked_routes": [
            {"from":"指挥部","to":"实皆村","via":"南线公路","block_type":"桥梁断裂","block_location":"南桥","detour":"绕行北线"}
        ],
        "hazard_zones": [
            {"location":"东山坡","hazard_type":"滑坡风险","severity":"high","advice":"禁止通行"}
        ],
        "recommended_routes": [
            {"route":"北线公路","reason":"路面完好且路程最短","priority":1}
        ]
    }
    """

    # 发现的灾情要素
    discovered_elements = Column(JSON)  # [{"type":"building_collapse","count":12,"severity":"high"},
                                        #   {"type":"road_damage","count":5,"severity":"medium"},
                                        #   {"type":"survivor_signal","count":3,"location":"..."}]

    # 结构研判（对接 Qwen-VL）
    structure_analysis = Column(JSON)                          # 建筑结构分析结果
    survivor_signals = Column(JSON)                           # 发现的生命迹象

    # 状态
    status = Column(String(20), default="pending")             # pending/in_progress/analyzed/completed
    analyzed_at = Column(DateTime)
    analyzed_by = Column(String(50), default="Qwen-VL")        # 分析模型

    # 关联
    disaster_id = Column(Integer, ForeignKey("disasters.id"), nullable=True)
    hotspot_id = Column(Integer, ForeignKey("disaster_hotspots.id"), nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
