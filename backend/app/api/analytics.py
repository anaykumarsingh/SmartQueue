from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analytics import AnalyticsResponse
from app.services.analytics_service import get_service_analytics


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/{service_id}", response_model=AnalyticsResponse)
def read_service_analytics(
    service_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_service_analytics(db, service_id)

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )
