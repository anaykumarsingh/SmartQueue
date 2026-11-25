from sqlalchemy.orm import Session

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

    if token.status != "waiting":
        return {
            "token_number": token.token_number,
            "status": token.status,
            "people_ahead": 0,
            "estimated_wait_minutes": 0.0,
        }

    people_ahead_tokens = (
        db.query(QueueToken)
        .filter(
            QueueToken.service_id == token.service_id,
            QueueToken.status == "waiting",
            QueueToken.id < token.id,
        )
        .order_by(QueueToken.id)
        .all()
    )

    people_ahead = len(people_ahead_tokens)

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

    counters = (
        db.query(Counter)
        .filter(
            Counter.service_id == token.service_id,
            Counter.status == "open",
        )
        .all()
    )

    if not counters:
        counter_loads = {None: 0.0}
    else:
        counter_loads = {counter.id: 0.0 for counter in counters}

    serving_tokens = (
        db.query(QueueToken)
        .filter(
            QueueToken.service_id == token.service_id,
            QueueToken.status == "serving",
        )
        .all()
    )

    now = ist_now_naive()

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

    queue = people_ahead_tokens + [token]

    estimated_wait = 0.0

    for queued_token in queue:
        selected_counter = min(
            counter_loads,
            key=counter_loads.get,
        )

        estimated_wait = counter_loads[selected_counter]

        counter_loads[selected_counter] += average_service_time

    return {
        "token_number": token.token_number,
        "status": token.status,
        "people_ahead": people_ahead,
        "estimated_wait_minutes": round(estimated_wait, 2),
    }