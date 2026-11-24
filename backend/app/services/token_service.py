import hashlib
import secrets
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.queue import Counter, QueueToken, Service


IST = ZoneInfo("Asia/Kolkata")


def generate_token(db: Session, service_id: int):
    service = (
        db.query(Service)
        .filter(
            Service.id == service_id,
            Service.is_active.is_(True),
        )
        .first()
    )

    if service is None:
        raise ValueError("Selected service is unavailable.")

    now_aware = datetime.now(IST)
    now = now_aware.replace(tzinfo=None)

    expires_at = (
        now_aware.replace(hour=0, minute=0, second=0, microsecond=0)
        + timedelta(days=1)
    ).replace(tzinfo=None)

    # Find the next sequential number for this service.
    prefix = f"{service.code}_"

    existing_numbers = (
        db.query(QueueToken.token_number)
        .filter(QueueToken.service_id == service.id)
        .all()
    )

    sequence_numbers = []

    for (existing_number,) in existing_numbers:
        if existing_number.startswith(prefix):
            suffix = existing_number[len(prefix):]

            if suffix.isdigit():
                sequence_numbers.append(int(suffix))

    next_sequence = max(sequence_numbers, default=0) + 1
    token_number = f"{prefix}{next_sequence:03d}"

    # Generate a separate, unique six-digit verification number.
    for _ in range(100):
        verification_code = str(secrets.randbelow(900000) + 100000)

        exists = (
            db.query(QueueToken.id)
            .filter(QueueToken.verification_code == verification_code)
            .first()
        )

        if not exists:
            break
    else:
        raise ValueError("Could not generate a verification number. Try again.")

    # Generate a private QR secret; store only its SHA-256 hash.
    qr_secret = secrets.token_urlsafe(32)
    qr_hash = hashlib.sha256(qr_secret.encode("utf-8")).hexdigest()

    token = QueueToken(
        token_number=token_number,
        service_id=service.id,
        status="unclaimed",
        issued_at=now,
        qr_token_hash=qr_hash,
        expires_at=expires_at,
        verification_code=verification_code,
    )

    try:
        db.add(token)
        db.commit()
        db.refresh(token)
    except Exception:
        db.rollback()
        raise

    return {
        "id": token.id,
        "token_number": token.token_number,
        "service_id": token.service_id,
        "status": token.status,
        "estimated_wait_minutes": token.estimated_wait_minutes,
        "issued_at": token.issued_at,
        "verification_code": token.verification_code,
        "qr_code": qr_secret,
        "expires_at": token.expires_at,
    }


def verify_qr_token(db: Session, qr_code: str):
    qr_hash = hashlib.sha256(qr_code.encode("utf-8")).hexdigest()

    token = (
        db.query(QueueToken)
        .filter(QueueToken.qr_token_hash == qr_hash)
        .first()
    )

    if token is None:
        raise ValueError("Invalid QR code. Ticket not found.")

    now = datetime.now(IST).replace(tzinfo=None)

    if token.status == "expired":
        raise ValueError("This ticket has expired.")

    if token.status != "unclaimed":
        raise ValueError("This ticket has already been claimed or used.")

    if token.expires_at is None or now >= token.expires_at:
        token.status = "expired"
        db.commit()
        raise ValueError("This ticket has expired.")

    service = (
        db.query(Service)
        .filter(Service.id == token.service_id)
        .first()
    )

    if service is None:
        raise ValueError("Ticket service could not be found.")

    return {
        "token_number": token.token_number,
        "service_name": service.name,
        "status": token.status,
        "issued_at": token.issued_at,
        "expires_at": token.expires_at,
    }


def claim_qr_token(db: Session, qr_code: str):
    qr_hash = hashlib.sha256(qr_code.encode("utf-8")).hexdigest()
    now = datetime.now(IST).replace(tzinfo=None)

    # Atomically claim only a valid, unexpired, unclaimed ticket.
    result = db.execute(
        update(QueueToken)
        .where(
            QueueToken.qr_token_hash == qr_hash,
            QueueToken.status == "unclaimed",
            QueueToken.expires_at > now,
        )
        .values(
            status="waiting",
            claimed_at=now,
        )
    )

    if result.rowcount != 1:
        db.rollback()

        token = (
            db.query(QueueToken)
            .filter(QueueToken.qr_token_hash == qr_hash)
            .first()
        )

        if token is None:
            raise ValueError("Invalid QR code. Ticket not found.")

        if token.status != "unclaimed":
            raise ValueError("This ticket has already been claimed or used.")

        if token.expires_at is None or now >= token.expires_at:
            token.status = "expired"
            db.commit()
            raise ValueError("This ticket has expired.")

        raise ValueError("Ticket could not be claimed. Please try again.")

    db.commit()

    token = (
        db.query(QueueToken)
        .filter(QueueToken.qr_token_hash == qr_hash)
        .first()
    )

    return {
        "token_number": token.token_number,
        "status": token.status,
        "claimed_at": token.claimed_at,
    }



def _get_manual_ticket(db: Session, token_number: str, verification_code: str, counter_id: int):
    token = (
        db.query(QueueToken)
        .filter(QueueToken.token_number == token_number.strip())
        .first()
    )

    if token is None:
        raise ValueError("Ticket not found. Check the token number.")

    if not token.verification_code or not secrets.compare_digest(
        token.verification_code, verification_code
    ):
        raise ValueError("Incorrect verification code.")

    if token.status == "expired":
        raise ValueError("This ticket has expired.")

    if token.status != "unclaimed":
        raise ValueError("This ticket has already been claimed or used.")

    now = datetime.now(IST).replace(tzinfo=None)

    if token.expires_at is None or now >= token.expires_at:
        token.status = "expired"
        db.commit()
        raise ValueError("This ticket has expired.")

    counter = (
        db.query(Counter)
        .filter(Counter.id == counter_id)
        .first()
    )

    if counter is None:
        raise ValueError("Selected counter could not be found.")

    if counter.service_id != token.service_id:
        raise ValueError("This ticket belongs to a different service.")

    service = (
        db.query(Service)
        .filter(Service.id == token.service_id)
        .first()
    )

    if service is None:
        raise ValueError("Ticket service could not be found.")

    return token, service


def verify_manual_ticket(
    db: Session,
    token_number: str,
    verification_code: str,
    counter_id: int,
):
    token, service = _get_manual_ticket(
        db, token_number, verification_code, counter_id
    )

    return {
        "token_number": token.token_number,
        "service_id": token.service_id,
        "service_name": service.name,
        "status": token.status,
        "issued_at": token.issued_at,
        "expires_at": token.expires_at,
    }


def claim_manual_ticket(
    db: Session,
    token_number: str,
    verification_code: str,
    counter_id: int,
):
    token, _ = _get_manual_ticket(
        db, token_number, verification_code, counter_id
    )

    now = datetime.now(IST).replace(tzinfo=None)

    result = db.execute(
        update(QueueToken)
        .where(
            QueueToken.id == token.id,
            QueueToken.verification_code == verification_code,
            QueueToken.status == "unclaimed",
            QueueToken.expires_at > now,
        )
        .values(
            status="waiting",
            claimed_at=now,
        )
    )

    if result.rowcount != 1:
        db.rollback()
        raise ValueError(
            "Ticket could not be claimed. It may already have been used or expired."
        )

    db.commit()

    claimed_token = (
        db.query(QueueToken)
        .filter(QueueToken.id == token.id)
        .first()
    )

    return {
        "token_number": claimed_token.token_number,
        "status": claimed_token.status,
        "claimed_at": claimed_token.claimed_at,
    }
