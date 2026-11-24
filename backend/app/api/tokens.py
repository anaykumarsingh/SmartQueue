from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.token import (
    TokenCreate,
    QRTokenCreateResponse,
    TokenStatusResponse,
)
from app.services.token_service import generate_token
from app.services.queue_service import get_token_status


router = APIRouter(
    prefix="/tokens",
    tags=["Tokens"],
)


@router.post("/", response_model=QRTokenCreateResponse, status_code=201)
def create_token(
    token_data: TokenCreate,
    db: Session = Depends(get_db),
):
    try:
        return generate_token(
            db=db,
            service_id=token_data.service_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/{token_number}", response_model=TokenStatusResponse)
def read_token_status(
    token_number: str,
    db: Session = Depends(get_db),
):
    try:
        return get_token_status(db, token_number)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
