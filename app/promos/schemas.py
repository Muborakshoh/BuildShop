from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PromoCodeCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    user_id: int | None = Field(default=None, ge=1)  # ✅ персональный промокод
    discount_percent: Decimal | None = Field(default=None, ge=0, le=100)
    discount_amount: Decimal | None = Field(default=None, ge=0)
    min_order_amount: Decimal = Field(default=Decimal("0"), ge=0)
    max_discount: Decimal | None = Field(default=None, ge=0)
    usage_limit: int | None = Field(default=None, ge=1)
    is_active: bool = True
    valid_from: datetime | None = None
    valid_to: datetime | None = None


class PromoCodeUpdate(BaseModel):
    user_id: int | None = None
    discount_percent: Decimal | None = None
    discount_amount: Decimal | None = None
    min_order_amount: Decimal | None = Field(default=None, ge=0)
    max_discount: Decimal | None = None
    usage_limit: int | None = None
    is_active: bool | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None


class PromoCodeOut(BaseModel):
    id: int
    code: str
    user_id: int | None = None  # ✅
    discount_percent: Decimal | None
    discount_amount: Decimal | None
    min_order_amount: Decimal
    max_discount: Decimal | None
    usage_limit: int | None
    usage_count: int
    is_active: bool
    valid_from: datetime | None
    valid_to: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromoApplyRequest(BaseModel):
    code: str = Field(min_length=1)
    order_total: Decimal = Field(gt=0)


class PromoApplyResponse(BaseModel):
    code: str
    discount: Decimal
    new_total: Decimal
    description: str
