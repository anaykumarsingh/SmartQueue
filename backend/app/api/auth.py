from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.staff import Staff
from app.schemas.auth import (
    AccessTokenResponse,
    StaffCreateRequest,
    StaffLoginRequest,
    StaffResponse,
)
from app.services.auth_service import (
    authenticate_staff,
    create_staff_account,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/login", response_model=AccessTokenResponse)
def login(
    request: StaffLoginRequest,
    db: Session = Depends(get_db),
):
    result = authenticate_staff(
        db=db,
        username=request.username,
        password=request.password,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )

    return result


@router.post(
    "/staff",
    response_model=StaffResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_staff(
    request: StaffCreateRequest,
    db: Session = Depends(get_db),
    admin: Staff = Depends(get_current_admin),
):
    try:
        return create_staff_account(
            db=db,
            username=request.username,
            full_name=request.full_name,
            password=request.password,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )
