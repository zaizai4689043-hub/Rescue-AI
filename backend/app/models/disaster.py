import enum
from datetime import datetime
from typing import Any

from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DisasterType(str, enum.Enum):
    earthquake = "earthquake"
    aftershock = "aftershock"
    building_collapse = "building_collapse"
    road_damage = "road_damage"
    landslide = "landslide"
    secondary_hazard = "secondary_hazard"


class DisasterStatus(str, enum.Enum):
    reported = "reported"
    confirmed = "confirmed"
    processing = "processing"
    dispatched = "dispatched"  # 指挥长批准派遣后
    verify = "verify"          # 现场核验中
    resolved = "resolved"


class Disaster(Base):
    __tablename__ = "disasters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    disaster_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    disaster_level: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 特别重大/重大/较大/一般
    estimated_people_trapped: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_economic_loss: Mapped[float | None] = mapped_column(Float, nullable=True)  # 万元
    description: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=DisasterStatus.reported.value, nullable=False)
    reporter_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    image_urls: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    ai_analysis_result: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    reporter = relationship("User", back_populates="disasters", lazy="selectin")
