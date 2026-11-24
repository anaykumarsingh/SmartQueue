from datetime import datetime

from pydantic import BaseModel, ConfigDict


class QueueItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    token_number: str
    status: str
    counter_id: int | None
    issued_at: datetime
