from datetime import datetime
from typing import Optional, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.resource import Resource, ResourceStatus
from app.schemas.resource import ResourceCreate, ResourceUpdate, ResourceStatistics


def get_resources(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    resource_type: Optional[str] = None,
    status: Optional[str] = None,
) -> tuple[List[Resource], int]:
    query = db.query(Resource)
    if resource_type:
        query = query.filter(Resource.resource_type == resource_type)
    if status:
        query = query.filter(Resource.status == status)
    total = query.count()
    items = query.order_by(Resource.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def create_resource(db: Session, data: ResourceCreate) -> Resource:
    resource = Resource(**data.model_dump(exclude_unset=True))
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


def get_resource(db: Session, resource_id: int) -> Optional[Resource]:
    return db.query(Resource).filter(Resource.id == resource_id).first()


def update_resource(db: Session, resource: Resource, data: ResourceUpdate) -> Resource:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(resource, key, value)
    resource.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(resource)
    return resource


def delete_resource(db: Session, resource: Resource) -> None:
    db.delete(resource)
    db.commit()


def dispatch_resource(db: Session, resource: Resource, target_location: str, quantity: Optional[int] = None) -> Resource:
    if quantity is not None and quantity < resource.quantity:
        resource.quantity -= quantity
    else:
        resource.status = ResourceStatus.dispatched.value
    resource.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(resource)
    return resource


def get_statistics(db: Session) -> ResourceStatistics:
    total_count = db.query(Resource).count()

    type_rows = (
        db.query(Resource.resource_type, func.count(Resource.id))
        .group_by(Resource.resource_type)
        .all()
    )
    by_type = {row[0]: row[1] for row in type_rows}

    status_rows = (
        db.query(Resource.status, func.count(Resource.id))
        .group_by(Resource.status)
        .all()
    )
    by_status = {row[0]: row[1] for row in status_rows}

    return ResourceStatistics(
        total_count=total_count,
        by_type=by_type,
        by_status=by_status,
    )
