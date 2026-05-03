from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(default="", max_length=140)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)


class CategoryRead(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(default="", max_length=280)
    description: str = Field(default="—")
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    image_url: str | None = Field(default=None, max_length=500)
    unit: str = Field(default="шт", max_length=20)
    volume: str | None = Field(default=None, max_length=50)


class ProductCreate(ProductBase):
    initial_stock: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=280)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    image_url: str | None = Field(default=None, max_length=500)
    unit: str | None = Field(default=None, max_length=20)
    volume: str | None = Field(default=None, max_length=50)


class ProductRead(ProductBase):
    id: int
    category: CategoryRead
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListItem(ProductRead):
    stock_quantity: int = 0
