from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.staff import Staff


def create_staff_account(
    db: Session,
    username: str,
    full_name: str,
    password: str,
    is_admin: bool = False,
) -> Staff:
    username = username.strip().lower()
    full_name = full_name.strip()

    existing_staff = db.scalar(
        select(Staff).where(Staff.username == username)
    )

    if existing_staff:
        raise ValueError("This username is already registered.")

    staff = Staff(
        username=username,
        full_name=full_name,
        password_hash=hash_password(password),
        is_active=True,
        is_admin=is_admin,
    )

    db.add(staff)
    db.commit()
    db.refresh(staff)

    return staff


def authenticate_staff(
    db: Session,
    username: str,
    password: str,
):
    username = username.strip().lower()

    staff = db.scalar(
        select(Staff).where(Staff.username == username)
    )

    if not staff or not verify_password(password, staff.password_hash):
        return None

    if not staff.is_active:
        return None

    access_token = create_access_token(str(staff.id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "staff": staff,
    }
