from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_staff
from app.models.staff import Staff
from app.schemas.staff import CallNextRequest
from app.schemas.token import (
    TokenResponse,
    ManualTicketRequest,
    ManualTicketVerifyResponse,
    ManualTicketClaimResponse,
)
from app.services.staff_service import call_next_token, complete_current_token
from app.services.token_service import verify_manual_ticket, claim_manual_ticket


router = APIRouter(
    prefix="/staff",
    tags=["Staff"],
)


@router.post("/call-next", response_model=TokenResponse)
def call_next(
    request: CallNextRequest,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
):
    try:
        return call_next_token(db=db, counter_id=request.counter_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/complete", response_model=TokenResponse)
def complete_token(
    request: CallNextRequest,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
):
    try:
        return complete_current_token(db=db, counter_id=request.counter_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/verify-ticket", response_model=ManualTicketVerifyResponse)
def verify_ticket(
    request: ManualTicketRequest,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
):
    try:
        return verify_manual_ticket(
            db=db,
            token_number=request.token_number,
            verification_code=request.verification_code,
            counter_id=request.counter_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/claim-ticket", response_model=ManualTicketClaimResponse)
def claim_ticket(
    request: ManualTicketRequest,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
):
    try:
        return claim_manual_ticket(
            db=db,
            token_number=request.token_number,
            verification_code=request.verification_code,
            counter_id=request.counter_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
