from datetime import datetime
from typing import Optional, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.trapped_person import TrappedPerson
from app.schemas.trapped_person import TrappedPersonCreate, TrappedPersonUpdate, TrappedPersonStatistics


def get_trapped_persons(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    disaster_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
) -> tuple[List[TrappedPerson], int]:
    query = db.query(TrappedPerson)
    if disaster_id:
        query = query.filter(TrappedPerson.disaster_id == disaster_id)
    if status:
        query = query.filter(TrappedPerson.status == status)
    if priority:
        query = query.filter(TrappedPerson.priority == priority)
    total = query.count()
    items = query.order_by(TrappedPerson.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def create_trapped_person(db: Session, data: TrappedPersonCreate) -> TrappedPerson:
    person = TrappedPerson(**data.model_dump(exclude_unset=True))
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


def get_trapped_person(db: Session, person_id: int) -> Optional[TrappedPerson]:
    return db.query(TrappedPerson).filter(TrappedPerson.id == person_id).first()


def update_trapped_person(db: Session, person: TrappedPerson, data: TrappedPersonUpdate) -> TrappedPerson:
    update_data = data.model_dump(exclude_unset=True)
    # 如果状态变更为 rescued，自动记录 rescued_at
    if update_data.get("status") == "rescued" and person.status != "rescued":
        person.rescued_at = datetime.utcnow()
    for key, value in update_data.items():
        setattr(person, key, value)
    person.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(person)
    return person


def rescue_trapped_person(db: Session, person: TrappedPerson) -> TrappedPerson:
    person.status = "rescued"
    person.rescued_at = datetime.utcnow()
    person.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(person)
    return person


def delete_trapped_person(db: Session, person: TrappedPerson) -> None:
    db.delete(person)
    db.commit()


def get_statistics(db: Session, disaster_id: Optional[int] = None) -> TrappedPersonStatistics:
    query = db.query(TrappedPerson)
    if disaster_id:
        query = query.filter(TrappedPerson.disaster_id == disaster_id)

    total = query.count()

    status_rows = (
        query.with_entities(TrappedPerson.status, func.count(TrappedPerson.id))
        .group_by(TrappedPerson.status)
        .all()
    )
    by_status = {row[0]: row[1] for row in status_rows}

    priority_rows = (
        query.with_entities(TrappedPerson.priority, func.count(TrappedPerson.id))
        .group_by(TrappedPerson.priority)
        .all()
    )
    by_priority = {row[0]: row[1] for row in priority_rows}

    rescued = by_status.get("rescued", 0)
    rescue_rate = round(rescued / total * 100, 1) if total > 0 else 0.0

    return TrappedPersonStatistics(
        total=total,
        by_status=by_status,
        by_priority=by_priority,
        rescue_rate=rescue_rate,
    )
