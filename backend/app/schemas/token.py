from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TokenCreate(BaseModel):
    service_id: int = Field(gt=0)


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    token_number: str
    service_id: int
    status: str
    estimated_wait_minutes: float | None
    issued_at: datetime


class QRTokenCreateResponse(TokenResponse):
    qr_code: str
    verification_code: str
    expires_at: datetime


class TokenStatusResponse(BaseModel):
    token_number: str
    status: str
    people_ahead: int
    estimated_wait_minutes: float


class QRVerifyRequest(BaseModel):
    qr_code: str = Field(min_length=20, max_length=200)


class QRVerifyResponse(BaseModel):
    token_number: str
    service_name: str
    status: str
    issued_at: datetime
    expires_at: datetime


class QRClaimResponse(BaseModel):
    token_number: str
    status: str
    claimed_at: datetime


class ManualTicketRequest(BaseModel):
    token_number: str = Field(min_length=3, max_length=30)
    verification_code: str = Field(pattern=r"^\d{6}$")
    counter_id: int = Field(gt=0)


class ManualTicketVerifyResponse(BaseModel):
    token_number: str
    service_id: int
    service_name: str
    status: str
    issued_at: datetime
    expires_at: datetime


class ManualTicketClaimResponse(BaseModel):
    token_number: str
    status: str
    claimed_at: datetime
