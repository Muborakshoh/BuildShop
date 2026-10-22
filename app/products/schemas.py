from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.translations import translations_validator


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(default="", max_length=140)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    translations: str | None = None  # JSON string

    _validate_translations = translations_validator("translations")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    translations: str | None = None

    _validate_translations = translations_validator("translations")


class CategoryRead(CategoryBase):
    id: int
    translations: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(default="", max_length=280)
    description: str = Field(default="—")
    price: Decimal = Field(gt=0)
    image_url: str | None = Field(default=None, max_length=500)
    meta_title: str | None = Field(default=None, max_length=255)
    meta_description: str | None = Field(default=None, max_length=500)
    og_image: str | None = Field(default=None, max_length=500)
    robots_index: bool = True
    canonical_url: str | None = Field(default=None, max_length=500)
    unit: str = Field(default="шт", max_length=20)
    volume: str | None = Field(default=None, max_length=50)
    coverage_per_unit_m2: Decimal | None = Field(default=None, gt=0)
    units_per_pack: Decimal = Field(default=Decimal("1"), gt=0)
    calc_waste_percent: Decimal = Field(default=Decimal("10"), ge=0, le=100)
    translations: str | None = None  # JSON string

    _validate_translations = translations_validator("translations")


class ProductCreate(ProductBase):
    initial_stock: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=280)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0)
    image_url: str | None = Field(default=None, max_length=500)
    meta_title: str | None = Field(default=None, max_length=255)
    meta_description: str | None = Field(default=None, max_length=500)
    og_image: str | None = Field(default=None, max_length=500)
    robots_index: bool | None = None
    canonical_url: str | None = Field(default=None, max_length=500)
    unit: str | None = Field(default=None, max_length=20)
    volume: str | None = Field(default=None, max_length=50)
    coverage_per_unit_m2: Decimal | None = Field(default=None, gt=0)
    units_per_pack: Decimal | None = Field(default=None, gt=0)
    calc_waste_percent: Decimal | None = Field(default=None, ge=0, le=100)
    translations: str | None = None

    _validate_translations = translations_validator("translations")


class ProductRead(ProductBase):
    id: int
    category: CategoryRead
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListItem(ProductRead):
    stock_quantity: int = 0
