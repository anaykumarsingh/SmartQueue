from pydantic import BaseModel, Field


class CallNextRequest(BaseModel):
    counter_id: int = Field(gt=0)
