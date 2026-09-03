import enum
from datetime import datetime

from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DamageLevel(str, enum.Enum):
    minor = "minor"
    moderate = "moderate"
    severe = "severe"
    complete = "complete"


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    disaster_id: Mapped[int] = mapped_column(Integer, ForeignKey("disasters.id"), nullable=False)
    assessor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    damage_level: Mapped[str] = mapped_column(String(20), nullable=False)
    building_count_affected: Mapped[int] = mapped_column(Integer, default=0)
    casualty_estimate: Mapped[int] = mapped_column(Integer, default=0)
    injured_estimate: Mapped[int] = mapped_column(Integer, default=0)
    area_affected: Mapped[float] = mapped_column(Float, default=0.0)
    infrastructure_damage: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    disaster = relationship("Disaster", lazy="selectin")
    assessor = relationship("User", lazy="selectin")
