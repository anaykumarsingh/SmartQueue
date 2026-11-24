from datetime import datetime

from sqlalchemy.orm import Session

from app.models.queue import Counter, QueueToken


def call_next_token(db: Session, counter_id: int):
    counter = (
        db.query(Counter)
        .filter(Counter.id == counter_id)
        .first()
    )

    if counter is None:
        raise ValueError("Counter not found.")

    if counter.status != "open":
        raise ValueError("Counter is not open.")

    current_token = (
        db.query(QueueToken)
        .filter(
            QueueToken.counter_id == counter_id,
            QueueToken.status == "serving",
        )
        .first()
    )

    if current_token is not None:
        raise ValueError("This counter is already serving a token.")

    token = (
        db.query(QueueToken)
        .filter(
            QueueToken.service_id == counter.service_id,
            QueueToken.status == "waiting",
        )
        .order_by(QueueToken.id)
        .first()
    )

    if token is None:
        raise ValueError("No waiting tokens available.")

    token.status = "serving"
    token.counter_id = counter_id
    token.called_at = datetime.now()

    db.commit()
    db.refresh(token)

    return token

from app.models.queue import ServiceRecord


def complete_current_token(db: Session, counter_id: int):
    counter = (
        db.query(Counter)
        .filter(Counter.id == counter_id)
        .first()
    )

    if counter is None:
        raise ValueError("Counter not found.")

    token = (
        db.query(QueueToken)
        .filter(
            QueueToken.counter_id == counter_id,
            QueueToken.status == "serving",
        )
        .first()
    )

    if token is None:
        raise ValueError("No token is currently being served at this counter.")

    now = datetime.now()
    started_at = token.called_at or now

    waiting_minutes = max(
        0,
        (started_at - token.issued_at).total_seconds() / 60,
    )

    service_minutes = max(
        0,
        (now - started_at).total_seconds() / 60,
    )

    token.status = "completed"
    token.completed_at = now

    record = ServiceRecord(
        token_id=token.id,
        counter_id=counter_id,
        waiting_time_minutes=round(waiting_minutes, 2),
        service_time_minutes=round(service_minutes, 2),
        started_at=started_at,
        ended_at=now,
    )

    db.add(record)
    db.commit()
    db.refresh(token)

    return token
