"""Delivery zones and pricing — stored in DB, managed via admin."""

from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DeliveryZone(Base):
    __tablename__ = "delivery_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)  # e.g. "Душанбе центр"
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)  # delivery price
    min_order_for_free: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))  # free delivery threshold
    estimated_days: Mapped[str | None] = mapped_column(String(20))  # e.g. "1-2 рӯз"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    translations: Mapped[str | None] = mapped_column(Text)  # JSON multilingual
