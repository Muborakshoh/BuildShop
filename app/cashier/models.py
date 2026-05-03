import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CashShiftStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class CashOperationType(str, enum.Enum):
    SALE = "sale"
    REFUND = "refund"
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    MIXED = "mixed"


class CashShift(Base):
    __tablename__ = "cash_shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    register_name: Mapped[str] = mapped_column(String(120), nullable=False)
    opened_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    closed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[CashShiftStatus] = mapped_column(Enum(CashShiftStatus), default=CashShiftStatus.OPEN, nullable=False)
    opening_cash: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    expected_cash: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    actual_cash: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    opened_by = relationship("User", foreign_keys=[opened_by_id], back_populates="cash_shifts")
    closed_by = relationship("User", foreign_keys=[closed_by_id])
    transactions = relationship("CashTransaction", back_populates="shift", cascade="all, delete-orphan")


class CashTransaction(Base):
    __tablename__ = "cash_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    shift_id: Mapped[int] = mapped_column(ForeignKey("cash_shifts.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    operation_type: Mapped[CashOperationType] = mapped_column(Enum(CashOperationType), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cash_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    card_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    receipt_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    shift = relationship("CashShift", back_populates="transactions")
    seller = relationship("User", back_populates="cash_transactions")
    items = relationship("CashTransactionItem", back_populates="transaction", cascade="all, delete-orphan")


class CashTransactionItem(Base):
    __tablename__ = "cash_transaction_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("cash_transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    transaction = relationship("CashTransaction", back_populates="items")
    product = relationship("Product")
