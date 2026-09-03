from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.dependencies import get_current_active_user
from app.schemas.user import UserResponse

router = APIRouter(tags=["用户管理"])


@router.get("/", response_model=List[UserResponse])
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != UserRole.admin.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
    users = db.query(User).offset((page - 1) * page_size).limit(page_size).all()
    return users


@router.put("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != UserRole.admin.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可操作")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    new_role = body.get("role")
    if not new_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 role 字段")
    valid_roles = [e.value for e in UserRole]
    if new_role not in valid_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"无效角色: {new_role}，可选: {valid_roles}")
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/toggle-active", response_model=UserResponse)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != UserRole.admin.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可操作")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user
