
from pydantic import BaseModel, ConfigDict


class CounterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    counter_number: int
    label: str
    status: str
