from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
    ResourceListResponse,
    ResourceDispatch,
    ResourceStatistics,
)
from app.services import resource_service

router = APIRouter(tags=["资源管理"])


@router.get("/", response_model=ResourceListResponse)
def list_resources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    resource_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    items, total = resource_service.get_resources(
        db, page=page, page_size=page_size,
        resource_type=resource_type, status=status,
    )
    return ResourceListResponse(
        items=[ResourceResponse.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
def create_resource(
    data: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    resource = resource_service.create_resource(db, data)
    return ResourceResponse.model_validate(resource)


@router.get("/statistics", response_model=ResourceStatistics)
def statistics(db: Session = Depends(get_db)):
    return resource_service.get_statistics(db)


@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    resource = resource_service.get_resource(db, resource_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    return ResourceResponse.model_validate(resource)


@router.put("/{resource_id}", response_model=ResourceResponse)
def update_resource(
    resource_id: int,
    data: ResourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    resource = resource_service.get_resource(db, resource_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    updated = resource_service.update_resource(db, resource, data)
    return ResourceResponse.model_validate(updated)


@router.patch("/{resource_id}/dispatch", response_model=ResourceResponse)
def dispatch_resource(
    resource_id: int,
    data: ResourceDispatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    resource = resource_service.get_resource(db, resource_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    if resource.status == "dispatched":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该资源已在调度中")
    updated = resource_service.dispatch_resource(db, resource, data.target_location, data.quantity)
    return ResourceResponse.model_validate(updated)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    resource = resource_service.get_resource(db, resource_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    resource_service.delete_resource(db, resource)
