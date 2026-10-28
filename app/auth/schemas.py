from pydantic import BaseModel, Field, field_validator

from app.core.validators import validate_email
from app.users.schemas import UserCreate, UserRead


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v: str) -> str:
        return validate_email(v)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterCodeRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v: str) -> str:
        return validate_email(v)


class RegisterCodeResponse(BaseModel):
    detail: str


class RegisterResponse(BaseModel):
    user: UserRead
    tokens: TokenPair


class RegisterRequest(UserCreate):
    verification_code: str = Field(min_length=4, max_length=12)
