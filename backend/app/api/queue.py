from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.queue import QueueToken, Service
from app.schemas.queue import QueueItemResponse


router = APIRouter(
    prefix="/queue",
    tags=["Queue"],
)


@router.get("/{service_id}", response_model=list[QueueItemResponse])
def get_service_queue(
    service_id: int,
    db: Session = Depends(get_db),
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id)
        .first()
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found.",
        )

    return (
        db.query(QueueToken)
        .filter(
            QueueToken.service_id == service_id,
            QueueToken.status.in_(["waiting", "serving"]),
        )
        .order_by(QueueToken.id)
        .all()
    )
