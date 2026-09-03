from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.volunteer import (
    VolunteerCreate,
    VolunteerUpdate,
    VolunteerResponse,
    VolunteerListResponse,
    VolunteerAssign,
    VolunteerStatistics,
)
from app.models.volunteer import Volunteer
from app.services import volunteer_service

router = APIRouter(tags=["志愿者管理"])


@router.get("/", response_model=VolunteerListResponse)
def list_volunteers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    skills: Optional[str] = None,
    db: Session = Depends(get_db),
):
    skills_list = [s.strip() for s in skills.split(",") if s.strip()] if skills else None
    items, total = volunteer_service.get_volunteers(
        db, page=page, page_size=page_size,
        status=status, skills=skills_list,
    )
    return VolunteerListResponse(
        items=[VolunteerResponse.model_validate(v) for v in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=VolunteerResponse, status_code=status.HTTP_201_CREATED)
def create_volunteer(
    data: VolunteerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    existing = db.query(Volunteer).filter_by(user_id=data.user_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该用户已是志愿者")
    volunteer = volunteer_service.create_volunteer(db, data)
    return VolunteerResponse.model_validate(volunteer)


@router.get("/statistics", response_model=VolunteerStatistics)
def statistics(db: Session = Depends(get_db)):
    return volunteer_service.get_statistics(db)


@router.get("/match", response_model=List[VolunteerResponse])
def match_volunteers(
    skills: str = Query(..., description="逗号分隔的技能列表"),
    db: Session = Depends(get_db),
):
    skills_list = [s.strip() for s in skills.split(",") if s.strip()]
    if not skills_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供至少一项技能")
    volunteers = volunteer_service.match_by_skills(db, skills_list)
    return [VolunteerResponse.model_validate(v) for v in volunteers]


@router.get("/{volunteer_id}", response_model=VolunteerResponse)
def get_volunteer(volunteer_id: int, db: Session = Depends(get_db)):
    volunteer = volunteer_service.get_volunteer(db, volunteer_id)
    if not volunteer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志愿者不存在")
    return VolunteerResponse.model_validate(volunteer)


@router.put("/{volunteer_id}", response_model=VolunteerResponse)
def update_volunteer(
    volunteer_id: int,
    data: VolunteerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    volunteer = volunteer_service.get_volunteer(db, volunteer_id)
    if not volunteer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志愿者不存在")
    updated = volunteer_service.update_volunteer(db, volunteer, data)
    return VolunteerResponse.model_validate(updated)


@router.patch("/{volunteer_id}/assign", response_model=VolunteerResponse)
def assign_volunteer(
    volunteer_id: int,
    data: VolunteerAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    volunteer = volunteer_service.get_volunteer(db, volunteer_id)
    if not volunteer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志愿者不存在")
    if volunteer.status == "on_mission":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该志愿者已在任务中")
    updated = volunteer_service.assign_volunteer(db, volunteer, data.task_description, data.location)
    return VolunteerResponse.model_validate(updated)


@router.delete("/{volunteer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_volunteer(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    volunteer = volunteer_service.get_volunteer(db, volunteer_id)
    if not volunteer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志愿者不存在")
    volunteer_service.delete_volunteer(db, volunteer)
