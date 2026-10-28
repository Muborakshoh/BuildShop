from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.orders.models import OrderStatus


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=1000)


class OrderCreate(BaseModel):
    delivery_method: str = Field(default="pickup", pattern="^(pickup|delivery)$")
    delivery_address: str = Field(default="Самовывоз", min_length=1, max_length=500)
    delivery_zone_id: int | None = None
    payment_method: str = Field(default="cash", pattern="^(cash|transfer)$")
    phone: str | None = Field(default=None, max_length=30)
    comment: str | None = Field(default=None, max_length=2000)
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemRead(BaseModel):
    id: int
    product_id: int | None = None
    product_name: str | None = None
    quantity: int
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class StatusHistoryRead(BaseModel):
    id: int
    old_status: str | None
    new_status: str
    comment: str | None
    changed_by: int | None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: int
    user_id: int
    status: OrderStatus
    total_amount: Decimal
    payment_method: str
    delivery_method: str
    delivery_address: str
    delivery_zone_id: int | None = None
    delivery_price: Decimal
    phone: str | None
    comment: str | None
    items: list[OrderItemRead]
    status_history: list[StatusHistoryRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    comment: str | None = Field(default=None, max_length=500)

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=1000)


class CartItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    product_name: str | None = None
    product_price: Decimal | None = None

    model_config = ConfigDict(from_attributes=True)
