from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.trapped_person import (
    TrappedPersonCreate,
    TrappedPersonUpdate,
    TrappedPersonResponse,
    TrappedPersonListResponse,
    TrappedPersonStatistics,
)
from app.services import trapped_person_service

router = APIRouter(tags=["受困者追踪"])


@router.get("/", response_model=TrappedPersonListResponse)
def list_trapped_persons(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    disaster_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
):
    items, total = trapped_person_service.get_trapped_persons(
        db, page=page, page_size=page_size,
        disaster_id=disaster_id, status=status, priority=priority,
    )
    return TrappedPersonListResponse(
        items=[TrappedPersonResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=TrappedPersonResponse, status_code=status.HTTP_201_CREATED)
def create_trapped_person(
    data: TrappedPersonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    person = trapped_person_service.create_trapped_person(db, data)
    return TrappedPersonResponse.model_validate(person)


@router.get("/statistics", response_model=TrappedPersonStatistics)
def statistics(
    disaster_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    return trapped_person_service.get_statistics(db, disaster_id=disaster_id)


@router.get("/{person_id}", response_model=TrappedPersonResponse)
def get_trapped_person(person_id: int, db: Session = Depends(get_db)):
    person = trapped_person_service.get_trapped_person(db, person_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="受困者记录不存在")
    return TrappedPersonResponse.model_validate(person)


@router.put("/{person_id}", response_model=TrappedPersonResponse)
def update_trapped_person(
    person_id: int,
    data: TrappedPersonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    person = trapped_person_service.get_trapped_person(db, person_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="受困者记录不存在")
    updated = trapped_person_service.update_trapped_person(db, person, data)
    return TrappedPersonResponse.model_validate(updated)


@router.patch("/{person_id}/rescue", response_model=TrappedPersonResponse)
def rescue_trapped_person(
    person_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    person = trapped_person_service.get_trapped_person(db, person_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="受困者记录不存在")
    updated = trapped_person_service.rescue_trapped_person(db, person)
    return TrappedPersonResponse.model_validate(updated)


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trapped_person(
    person_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    person = trapped_person_service.get_trapped_person(db, person_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="受困者记录不存在")
    trapped_person_service.delete_trapped_person(db, person)
