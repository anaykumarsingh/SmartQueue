from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.queue import Service
from app.schemas.service import ServiceResponse


router = APIRouter(
    prefix="/services",
    tags=["Services"],
)


@router.get("/", response_model=list[ServiceResponse])
def get_services(db: Session = Depends(get_db)):
    return (
        db.query(Service)
        .filter(Service.is_active == True)
        .order_by(Service.id)
        .all()
    )
