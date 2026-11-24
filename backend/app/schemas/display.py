from pydantic import BaseModel


class ServingToken(BaseModel):
    token_number: str
    counter_label: str


class WaitingToken(BaseModel):
    token_number: str
    position: int


class PublicDisplayResponse(BaseModel):
    service_id: int
    service_name: str
    currently_serving: list[ServingToken]
    waiting_tokens: list[WaitingToken]
    total_waiting: int
