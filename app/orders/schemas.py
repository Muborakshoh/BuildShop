from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.orders.models import OrderStatus


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=1000)


class OrderCreate(BaseModel):
    delivery_address: str = Field(default="Самовывоз", min_length=1, max_length=500)
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: int
    user_id: int
    status: OrderStatus
    total_amount: Decimal
    delivery_address: str
    items: list[OrderItemRead]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus

