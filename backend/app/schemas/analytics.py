from pydantic import BaseModel


class AnalyticsResponse(BaseModel):
    service_id: int
    service_name: str
    total_tokens: int
    completed_tokens: int
    waiting_tokens: int
    average_waiting_minutes: float
    average_service_minutes: float
    open_counters: int
