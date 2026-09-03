from datetime import datetime
from typing import Any

from sqlalchemy import String, Integer, Float, Text, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SocialPost(Base):
    """社情帖统一存储表：各平台适配器产出经 raw_ref 哈希去重后落库。

    口径说明：
    - raw_ref：sha256("{platform}:{post_id|text}")，唯一约束，重复入库直接跳过；
    - ts：帖子发布时间（北京时间口径的 naive datetime，可为空）；
    - signal_type/urgency_hint：归一后的信号类型与派生紧急度（见
      app/services/social/adapters.py），非平台原始字段。
    """

    __tablename__ = "social_posts"
    __table_args__ = (
        Index("ix_social_posts_platform_signal", "platform", "signal_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # weibo/douyin/xiaohongshu
    post_id: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 平台内原帖 id（可为空）
    raw_ref: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)  # 去重哈希
    text: Mapped[str] = mapped_column(Text, nullable=False)
    ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 发布时间
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    geo_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    signal_type: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-1
    urgency_hint: Mapped[str | None] = mapped_column(String(16), nullable=True)  # high/medium/low
    tags: Mapped[Any | None] = mapped_column(JSON, nullable=True)  # 话题词/命中关键词
    offset_min: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 震后分钟偏移（回放口径）
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
