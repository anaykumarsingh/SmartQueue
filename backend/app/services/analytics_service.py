from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.queue import (
    Service,
    Counter,
    QueueToken,
    ServiceRecord,
)


def get_service_analytics(db: Session, service_id: int):
    service = (
        db.query(Service)
        .filter(Service.id == service_id)
        .first()
    )

    if service is None:
        raise ValueError("Service not found.")

    total_tokens = (
        db.query(QueueToken)
        .filter(QueueToken.service_id == service_id)
        .count()
    )

    completed_tokens = (
        db.query(QueueToken)
        .filter(
            QueueToken.service_id == service_id,
            QueueToken.status == "completed",
        )
        .count()
    )

    waiting_tokens = (
        db.query(QueueToken)
        .filter(
            QueueToken.service_id == service_id,
            QueueToken.status == "waiting",
        )
        .count()
    )

    average_waiting = (
        db.query(func.avg(ServiceRecord.waiting_time_minutes))
        .join(QueueToken, ServiceRecord.token_id == QueueToken.id)
        .filter(QueueToken.service_id == service_id)
        .scalar()
    )

    average_service = (
        db.query(func.avg(ServiceRecord.service_time_minutes))
        .join(QueueToken, ServiceRecord.token_id == QueueToken.id)
        .filter(QueueToken.service_id == service_id)
        .scalar()
    )

    open_counters = (
        db.query(Counter)
        .filter(
            Counter.service_id == service_id,
            Counter.status == "open",
        )
        .count()
    )

    return {
        "service_id": service.id,
        "service_name": service.name,
        "total_tokens": total_tokens,
        "completed_tokens": completed_tokens,
        "waiting_tokens": waiting_tokens,
        "average_waiting_minutes": round(average_waiting or 0, 2),
        "average_service_minutes": round(average_service or 0, 2),
        "open_counters": open_counters,
    }
