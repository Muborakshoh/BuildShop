from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class DeliveryZoneRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: Decimal
    min_order_for_free: Decimal | None = None
    estimated_days: str | None = None
    is_active: bool
    translations: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DeliveryZoneCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    price: Decimal = Field(ge=0)
    min_order_for_free: Decimal | None = Field(default=None, ge=0)
    estimated_days: str | None = Field(default=None, max_length=20)
    is_active: bool = True
    sort_order: int = 0
    translations: str | None = None


class DeliveryZoneUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    min_order_for_free: Decimal | None = Field(default=None, ge=0)
    estimated_days: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None
    translations: str | None = None


class DeliveryCalcRequest(BaseModel):
    zone_id: int
    order_total: Decimal = Field(ge=0)


class DeliveryCalcResponse(BaseModel):
    zone_name: str
    delivery_price: Decimal
    is_free: bool
    estimated_days: str | None = None
