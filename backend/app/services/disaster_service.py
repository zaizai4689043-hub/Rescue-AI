from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import func, String
from sqlalchemy.orm import Session

from app.models.disaster import Disaster
from app.schemas.disaster import DisasterCreate, DisasterUpdate, DisasterStatistics, TrendItem


def get_disasters(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    disaster_type: Optional[str] = None,
    severity: Optional[int] = None,
) -> tuple[List[Disaster], int]:
    query = db.query(Disaster)
    if status:
        query = query.filter(Disaster.status == status)
    if disaster_type:
        query = query.filter(Disaster.disaster_type == disaster_type)
    if severity:
        query = query.filter(Disaster.severity == severity)
    total = query.count()
    items = query.order_by(Disaster.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def create_disaster(db: Session, disaster_in: DisasterCreate, reporter_id: int) -> Disaster:
    disaster = Disaster(
        **disaster_in.model_dump(exclude_unset=True),
        reporter_id=reporter_id,
    )
    db.add(disaster)
    db.commit()
    db.refresh(disaster)
    return disaster


def get_disaster(db: Session, disaster_id: int) -> Optional[Disaster]:
    return db.query(Disaster).filter(Disaster.id == disaster_id).first()


def update_disaster(db: Session, disaster: Disaster, disaster_in: DisasterUpdate) -> Disaster:
    update_data = disaster_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(disaster, key, value)
    disaster.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(disaster)
    return disaster


def delete_disaster(db: Session, disaster: Disaster) -> None:
    db.delete(disaster)
    db.commit()


def get_statistics(db: Session) -> DisasterStatistics:
    # Total count
    total_count = db.query(Disaster).count()

    # By status
    status_rows = (
        db.query(Disaster.status, func.count(Disaster.id))
        .group_by(Disaster.status)
        .all()
    )
    by_status = {row[0]: row[1] for row in status_rows}

    # By type
    type_rows = (
        db.query(Disaster.disaster_type, func.count(Disaster.id))
        .group_by(Disaster.disaster_type)
        .all()
    )
    by_type = {row[0]: row[1] for row in type_rows}

    # Recent 7 days trend
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    date_col = func.date(Disaster.created_at).label("date")
    trend_rows = (
        db.query(date_col, func.count(Disaster.id))
        .filter(Disaster.created_at >= seven_days_ago)
        .group_by(date_col)
        .order_by(date_col)
        .all()
    )
    recent_trend = [TrendItem(date=str(row[0]), count=row[1]) for row in trend_rows]

    return DisasterStatistics(
        total_count=total_count,
        by_status=by_status,
        by_type=by_type,
        recent_trend=recent_trend,
    )
