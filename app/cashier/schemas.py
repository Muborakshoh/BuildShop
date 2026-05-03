from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.cashier.models import CashOperationType, CashShiftStatus, PaymentMethod


class CashShiftOpen(BaseModel):
    register_name: str = Field(min_length=2, max_length=120)
    opening_cash: Decimal = Field(default=0, ge=0, max_digits=12, decimal_places=2)


class CashShiftClose(BaseModel):
    actual_cash: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class CashShiftRead(BaseModel):
    id: int
    register_name: str
    opened_by_id: int
    closed_by_id: int | None
    status: CashShiftStatus
    opening_cash: Decimal
    expected_cash: Decimal
    actual_cash: Decimal | None
    opened_at: datetime
    closed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class CashItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=1000)


class CashSaleCreate(BaseModel):
    payment_method: PaymentMethod
    cash_amount: Decimal = Field(default=0, ge=0, max_digits=12, decimal_places=2)
    card_amount: Decimal = Field(default=0, ge=0, max_digits=12, decimal_places=2)
    comment: str | None = Field(default=None, max_length=500)
    items: list[CashItemCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_payment(self) -> "CashSaleCreate":
        if self.payment_method == PaymentMethod.CASH and self.cash_amount <= 0:
            raise ValueError("cash_amount is required for cash payments")
        if self.payment_method == PaymentMethod.CARD and self.card_amount <= 0:
            raise ValueError("card_amount is required for card payments")
        if self.payment_method == PaymentMethod.MIXED and self.cash_amount + self.card_amount <= 0:
            raise ValueError("cash_amount or card_amount is required")
        return self


class CashTransactionItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class CashTransactionRead(BaseModel):
    id: int
    shift_id: int
    seller_id: int
    operation_type: CashOperationType
    payment_method: PaymentMethod
    total_amount: Decimal
    cash_amount: Decimal
    card_amount: Decimal
    receipt_number: str
    comment: str | None
    items: list[CashTransactionItemRead]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CashShiftSummary(BaseModel):
    shift: CashShiftRead
    sales_total: Decimal
    refunds_total: Decimal
    cash_total: Decimal
    card_total: Decimal
    receipt_count: int
