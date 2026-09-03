from datetime import datetime
from typing import Optional, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.volunteer import Volunteer, VolunteerStatus
from app.schemas.volunteer import VolunteerCreate, VolunteerUpdate, VolunteerStatistics


def get_volunteers(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    skills: Optional[List[str]] = None,
) -> tuple[List[Volunteer], int]:
    query = db.query(Volunteer)
    if status:
        query = query.filter(Volunteer.status == status)
    if skills:
        for skill in skills:
            query = query.filter(Volunteer.skills.contains(skill))
    total = query.count()
    items = query.order_by(Volunteer.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def create_volunteer(db: Session, data: VolunteerCreate) -> Volunteer:
    volunteer = Volunteer(**data.model_dump(exclude_unset=True))
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)
    return volunteer


def get_volunteer(db: Session, volunteer_id: int) -> Optional[Volunteer]:
    return db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()


def update_volunteer(db: Session, volunteer: Volunteer, data: VolunteerUpdate) -> Volunteer:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(volunteer, key, value)
    volunteer.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(volunteer)
    return volunteer


def delete_volunteer(db: Session, volunteer: Volunteer) -> None:
    db.delete(volunteer)
    db.commit()


def assign_volunteer(db: Session, volunteer: Volunteer, task_description: str, location: str) -> Volunteer:
    volunteer.status = VolunteerStatus.assigned.value
    volunteer.current_location = location
    volunteer.notes = task_description
    volunteer.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(volunteer)
    return volunteer


def match_by_skills(db: Session, skills_list: List[str]) -> List[Volunteer]:
    query = db.query(Volunteer).filter(Volunteer.status == VolunteerStatus.available.value)
    for skill in skills_list:
        query = query.filter(Volunteer.skills.contains(skill))
    return query.all()


def get_statistics(db: Session) -> VolunteerStatistics:
    total_count = db.query(Volunteer).count()

    status_rows = (
        db.query(Volunteer.status, func.count(Volunteer.id))
        .group_by(Volunteer.status)
        .all()
    )
    by_status = {row[0]: row[1] for row in status_rows}

    # Skill stats: fetch all skills and count
    all_volunteers = db.query(Volunteer.skills).all()
    by_skill: dict[str, int] = {}
    for (skills,) in all_volunteers:
        if skills:
            for skill in skills:
                by_skill[skill] = by_skill.get(skill, 0) + 1

    return VolunteerStatistics(
        total_count=total_count,
        by_status=by_status,
        by_skill=by_skill,
    )
