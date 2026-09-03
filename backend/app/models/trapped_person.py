import enum
from datetime import datetime

from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TrappedStatus(str, enum.Enum):
    waiting = "waiting"
    searching = "searching"
    rescued = "rescued"
    transferred = "transferred"


class TrappedPriority(str, enum.Enum):
    red = "red"
    yellow = "yellow"
    green = "green"
    black = "black"


class TrappedPerson(Base):
    __tablename__ = "trapped_persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    disaster_id: Mapped[int] = mapped_column(Integer, ForeignKey("disasters.id"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    location: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=TrappedStatus.waiting.value, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default=TrappedPriority.red.value, nullable=False)
    condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    rescued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    disaster = relationship("Disaster", lazy="selectin")
