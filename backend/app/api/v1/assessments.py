from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_active_user
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentUpdate,
    AssessmentResponse,
    AssessmentListResponse,
)
from app.services import assessment_service

router = APIRouter(tags=["灾情评估"])


@router.get("/", response_model=AssessmentListResponse)
def list_assessments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    disaster_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    items, total = assessment_service.get_assessments(
        db, page=page, page_size=page_size, disaster_id=disaster_id,
    )
    return AssessmentListResponse(
        items=[AssessmentResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(
    data: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    assessment = assessment_service.create_assessment(db, data, current_user.id)
    return AssessmentResponse.model_validate(assessment)


@router.get("/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    assessment = assessment_service.get_assessment(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评估记录不存在")
    return AssessmentResponse.model_validate(assessment)


@router.put("/{assessment_id}", response_model=AssessmentResponse)
def update_assessment(
    assessment_id: int,
    data: AssessmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    assessment = assessment_service.get_assessment(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评估记录不存在")
    updated = assessment_service.update_assessment(db, assessment, data)
    return AssessmentResponse.model_validate(updated)


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    assessment = assessment_service.get_assessment(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评估记录不存在")
    assessment_service.delete_assessment(db, assessment)
