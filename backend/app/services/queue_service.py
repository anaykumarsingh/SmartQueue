from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.time_utils import ist_now_naive
from app.models.queue import (
    QueueToken,
    Service,
    Counter,
    ServiceRecord,
)


def get_token_status(db: Session, token_number: str):
    token = (
        db.query(QueueToken)
        .filter(QueueToken.token_number == token_number)
        .first()
    )

    if token is None:
        raise ValueError("Token not found.")

    service = (
        db.query(Service)
        .filter(Service.id == token.service_id)
        .first()
    )

    if service is None:
        raise ValueError("Service not found.")

    if token.status not in ("unclaimed", "waiting"):
        return {
            "token_number": token.token_number,
            "status": token.status,
            "people_ahead": 0,
            "estimated_wait_minutes": 0.0,
        }

    now = ist_now_naive()

    # Include earlier waiting tokens and non-expired unclaimed tokens.
    active_queue_tokens = (
        db.query(QueueToken)
        .filter(
            QueueToken.service_id == token.service_id,
            QueueToken.id <= token.id,
            or_(
                QueueToken.status == "waiting",
                and_(
                    QueueToken.status == "unclaimed",
                    or_(
                        QueueToken.expires_at.is_(None),
                        QueueToken.expires_at > now,
                    ),
                ),
            ),
        )
        .order_by(QueueToken.id)
        .all()
    )

    people_ahead = sum(
        1 for queued_token in active_queue_tokens
        if queued_token.id < token.id
    )

    # Calculate average service duration from recent completed records.
    recent_records = (
        db.query(ServiceRecord.service_time_minutes)
        .join(
            QueueToken,
            ServiceRecord.token_id == QueueToken.id,
        )
        .filter(
            QueueToken.service_id == token.service_id,
            ServiceRecord.service_time_minutes > 0,
            ServiceRecord.service_time_minutes <= 60,
        )
        .order_by(ServiceRecord.ended_at.desc())
        .limit(20)
        .all()
    )

    durations = [record[0] for record in recent_records]

    average_service_time = (
        sum(durations) / len(durations)
        if durations
        else service.avg_service_minutes
    )

    # Start with the workload of currently open counters.
    counters = (
        db.query(Counter)
        .filter(
            Counter.service_id == token.service_id,
            Counter.status == "open",
        )
        .all()
    )

    if counters:
        counter_loads = {counter.id: 0.0 for counter in counters}
    else:
        # Fallback estimate when no counter is currently open.
        counter_loads = {None: 0.0}

    # Account for tokens currently being served.
    serving_tokens = (
        db.query(QueueToken)
        .filter(
            QueueToken.service_id == token.service_id,
            QueueToken.status == "serving",
        )
        .all()
    )

    for serving_token in serving_tokens:
        counter_id = serving_token.counter_id

        if counter_id not in counter_loads:
            counter_id = min(
                counter_loads,
                key=counter_loads.get,
            )

        elapsed = (
            (now - serving_token.called_at).total_seconds() / 60
            if serving_token.called_at
            else 0
        )

        remaining = max(
            average_service_time - elapsed,
            average_service_time * 0.25,
        )

        counter_loads[counter_id] += remaining

    # Assign each earlier token and the current token
    # to whichever counter is expected to become free first.
    estimated_wait = 0.0

    for queued_token in active_queue_tokens:
        selected_counter = min(
            counter_loads,
            key=counter_loads.get,
        )

        if queued_token.id == token.id:
            estimated_wait = counter_loads[selected_counter]

        counter_loads[selected_counter] += average_service_time

    return {
        "token_number": token.token_number,
        "status": token.status,
        "people_ahead": people_ahead,
        "estimated_wait_minutes": round(estimated_wait, 2),
    }
