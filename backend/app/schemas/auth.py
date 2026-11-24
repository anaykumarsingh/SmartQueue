from pydantic import BaseModel, Field


class StaffLoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=1, max_length=128)


class StaffCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=12, max_length=128)


class StaffResponse(BaseModel):
    id: int
    username: str
    full_name: str
    is_active: bool
    is_admin: bool

    model_config = {"from_attributes": True}


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    staff: StaffResponse
