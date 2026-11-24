from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.queue import Counter
from app.schemas.counter import CounterResponse

router = APIRouter(
    prefix="/counters",
    tags=["Counters"],
)


@router.get("/", response_model=list[CounterResponse])
def get_counters(db: Session = Depends(get_db)):
    return (
        db.query(Counter)
        .order_by(Counter.service_id, Counter.counter_number)
        .all()
    )
