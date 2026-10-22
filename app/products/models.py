from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))
    translations: Mapped[str | None] = mapped_column(Text)  # JSON: {"name_ru":"...","name_en":"...","desc_ru":"...","desc_en":"..."}

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(280), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500))
    meta_title: Mapped[str | None] = mapped_column(String(255))
    meta_description: Mapped[str | None] = mapped_column(String(500))
    og_image: Mapped[str | None] = mapped_column(String(500))
    robots_index: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    canonical_url: Mapped[str | None] = mapped_column(String(500))
    unit: Mapped[str] = mapped_column(String(20), default="шт", nullable=False, server_default="шт")
    volume: Mapped[str | None] = mapped_column(String(50))
    coverage_per_unit_m2: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    units_per_pack: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1"), server_default="1", nullable=False)
    calc_waste_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("10"), server_default="10", nullable=False)
    translations: Mapped[str | None] = mapped_column(Text)  # JSON multilingual
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    category = relationship("Category", back_populates="products")
    inventory = relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product", passive_deletes=True)
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan", passive_deletes=True)
    cash_transactions = relationship("CashTransactionItem", back_populates="product", passive_deletes=True)
