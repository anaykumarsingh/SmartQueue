from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.display import PublicDisplayResponse
from app.services.display_service import get_public_display


router = APIRouter(
    prefix="/display",
    tags=["Public Display"],
)


@router.get("/{service_id}", response_model=PublicDisplayResponse)
def read_public_display(
    service_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_public_display(db, service_id)

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )
