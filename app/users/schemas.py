from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.validators import validate_email
from app.users.models import UserRole


class UserCreate(BaseModel):
    email: str
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v: str) -> str:
        return validate_email(v)


class AdminUserCreate(BaseModel):
    email: str
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.BUYER

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v: str) -> str:
        return validate_email(v)


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None
    role: UserRole | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
