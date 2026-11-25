from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


def ist_now_naive() -> datetime:
    return datetime.now(IST).replace(tzinfo=None)


def ist_end_of_day_naive(now: datetime | None = None) -> datetime:
    now = now or datetime.now(IST).replace(tzinfo=None)
    if now.tzinfo is not None:
        now = now.astimezone(IST).replace(tzinfo=None)
    next_midnight = (
        now.replace(hour=0, minute=0, second=0, microsecond=0)
        + timedelta(days=1)
    )
    return next_midnight.replace(tzinfo=None)
