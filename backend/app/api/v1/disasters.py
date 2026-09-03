from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_active_user
from app.schemas.disaster import (
    DisasterCreate,
    DisasterUpdate,
    DisasterStatusUpdate,
    DisasterResponse,
    DisasterListResponse,
    DisasterStatistics,
    ALLOWED_TRANSITIONS,
)
from app.services import disaster_service

router = APIRouter(tags=["灾情管理"])


@router.get("/", response_model=DisasterListResponse)
def list_disasters(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    disaster_type: Optional[str] = None,
    severity: Optional[int] = None,
    db: Session = Depends(get_db),
):
    items, total = disaster_service.get_disasters(
        db, page=page, page_size=page_size,
        status=status, disaster_type=disaster_type, severity=severity,
    )
    return DisasterListResponse(
        items=[DisasterResponse.model_validate(d) for d in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=DisasterResponse, status_code=status.HTTP_201_CREATED)
def create_disaster(
    disaster_in: DisasterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    disaster = disaster_service.create_disaster(db, disaster_in, current_user.id)
    return DisasterResponse.model_validate(disaster)


@router.get("/statistics", response_model=DisasterStatistics)
def statistics(db: Session = Depends(get_db)):
    return disaster_service.get_statistics(db)


@router.get("/{disaster_id}", response_model=DisasterResponse)
def get_disaster(disaster_id: int, db: Session = Depends(get_db)):
    disaster = disaster_service.get_disaster(db, disaster_id)
    if not disaster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="灾情不存在")
    return DisasterResponse.model_validate(disaster)


@router.put("/{disaster_id}", response_model=DisasterResponse)
def update_disaster(
    disaster_id: int,
    disaster_in: DisasterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    disaster = disaster_service.get_disaster(db, disaster_id)
    if not disaster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="灾情不存在")
    # 仅 reporter 或 admin 可更新
    if disaster.reporter_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权更新此灾情")
    updated = disaster_service.update_disaster(db, disaster, disaster_in)
    return DisasterResponse.model_validate(updated)


@router.patch("/{disaster_id}/status", response_model=DisasterResponse)
def update_disaster_status(
    disaster_id: int,
    status_update: DisasterStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    disaster = disaster_service.get_disaster(db, disaster_id)
    if not disaster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="灾情不存在")
    new_status = status_update.status
    from app.models.disaster import DisasterStatus
    if new_status not in [e.value for e in DisasterStatus]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"无效状态: {new_status}")
    current = disaster.status
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"非法状态迁移: {current} → {new_status}（允许: {sorted(allowed) or '无'}）",
        )
    disaster.status = new_status
    from datetime import datetime
    disaster.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(disaster)
    return DisasterResponse.model_validate(disaster)


@router.delete("/{disaster_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_disaster(
    disaster_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    disaster = disaster_service.get_disaster(db, disaster_id)
    if not disaster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="灾情不存在")
    if disaster.reporter_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除此灾情")
    disaster_service.delete_disaster(db, disaster)
