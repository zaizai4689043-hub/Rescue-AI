from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate


def get_assessments(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    disaster_id: Optional[int] = None,
) -> tuple[List[Assessment], int]:
    query = db.query(Assessment)
    if disaster_id:
        query = query.filter(Assessment.disaster_id == disaster_id)
    total = query.count()
    items = query.order_by(Assessment.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def create_assessment(db: Session, data: AssessmentCreate, assessor_id: int) -> Assessment:
    assessment = Assessment(
        **data.model_dump(exclude_unset=True),
        assessor_id=assessor_id,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def get_assessment(db: Session, assessment_id: int) -> Optional[Assessment]:
    return db.query(Assessment).filter(Assessment.id == assessment_id).first()


def update_assessment(db: Session, assessment: Assessment, data: AssessmentUpdate) -> Assessment:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(assessment, key, value)
    assessment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assessment)
    return assessment


def delete_assessment(db: Session, assessment: Assessment) -> None:
    db.delete(assessment)
    db.commit()
