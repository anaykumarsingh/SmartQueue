from sqlalchemy.orm import Session

from app.models.queue import Service, QueueToken


def get_public_display(db: Session, service_id: int):
    service = (
        db.query(Service)
        .filter(Service.id == service_id)
        .first()
    )

    if service is None:
        raise ValueError("Service not found.")

    serving_tokens = (
        db.query(QueueToken)
        .filter(
            QueueToken.service_id == service_id,
            QueueToken.status == "serving",
        )
        .order_by(QueueToken.counter_id)
        .all()
    )

    waiting_tokens = (
        db.query(QueueToken)
        .filter(
            QueueToken.service_id == service_id,
            QueueToken.status == "waiting",
        )
        .order_by(QueueToken.id)
        .all()
    )

    return {
        "service_id": service.id,
        "service_name": service.name,
        "currently_serving": [
            {
                "token_number": token.token_number,
                "counter_label": token.counter.label,
            }
            for token in serving_tokens
        ],
        "waiting_tokens": [
            {
                "token_number": token.token_number,
                "position": position,
            }
            for position, token in enumerate(waiting_tokens, start=1)
        ],
        "total_waiting": len(waiting_tokens),
    }
