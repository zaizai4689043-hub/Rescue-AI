"""
微博数据模型
对应愿景 2：实时数据管道
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON
from sqlalchemy.sql import func

from app.database import Base


class WeiboPost(Base):
    """微博社情数据"""
    __tablename__ = "weibo_posts"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String(64), unique=True, nullable=False, index=True)  # 匿名哈希 ID
    text = Column(Text, nullable=False)                # 清洗后正文
    raw_text = Column(Text)                             # 原始正文（清洗前）
    published_at = Column(DateTime, nullable=False, index=True)  # 发布时间
    offset_min = Column(Float)                          # 相对发震的分钟偏移

    # NLP 处理结果
    ner_locations = Column(JSON)                        # [{name, lng, lat, confidence}]
    sentiment = Column(String(20), index=True)         # urgent/negative/neutral/hopeful
    damage_type = Column(String(30), index=True)       # 人员伤亡/房屋倒塌/道路中断/次生灾害/救援进展/震感反馈
    keywords = Column(JSON)                             # 命中关键词列表
    severity_vote = Column(Integer, default=1)          # 1-5 严重度
    credibility = Column(Float, default=0.5)            # 可信度评分 0-1

    # 来源
    source = Column(String(50), default="微博")
    source_type = Column(String(30), default="social_media")
    user_verified = Column(Boolean, default=False)      # 是否认证用户

    # 过滤状态
    is_filtered = Column(Boolean, default=False)        # 是否被噪声过滤
    filter_reason = Column(String(100))                 # 过滤原因：duplicate/rumor/bot/geo_out
    processed = Column(Boolean, default=False)          # NLP 是否已处理
    processed_at = Column(DateTime)

    # 是否包含呼救信号
    has_distress_signal = Column(Boolean, default=False)
    distress_keywords = Column(JSON)                    # ["救命","被困","紧急"]

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
