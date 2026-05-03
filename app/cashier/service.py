from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.cashier.models import CashOperationType, CashShift, CashShiftStatus, CashTransaction, CashTransactionItem, PaymentMethod
from app.cashier.repository import CashierRepository
from app.cashier.schemas import CashSaleCreate, CashShiftClose, CashShiftOpen, CashShiftSummary
from app.inventory.service import InventoryService
from app.products.repository import ProductRepository
from app.users.models import User


class CashierService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CashierRepository(db)
        self.products = ProductRepository(db)
        self.inventory = InventoryService(db)

    def open_shift(self, user: User, data: CashShiftOpen) -> CashShift:
        if self.repo.get_open_shift(data.register_name):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cash register already has an open shift")
        shift = CashShift(
            register_name=data.register_name,
            opened_by_id=user.id,
            opening_cash=data.opening_cash,
            expected_cash=data.opening_cash,
        )
        return self.repo.save_shift(shift)

    def current_shift(self, register_name: str | None = None) -> CashShift:
        shift = self.repo.get_open_shift(register_name)
        if not shift:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No open cash shift")
        return shift

    def close_shift(self, shift_id: int, user: User, data: CashShiftClose) -> CashShift:
        shift = self.repo.get_shift(shift_id)
        if not shift:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash shift not found")
        if shift.status == CashShiftStatus.CLOSED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cash shift already closed")
        shift.status = CashShiftStatus.CLOSED
        shift.closed_by_id = user.id
        shift.actual_cash = data.actual_cash
        shift.closed_at = datetime.now(UTC)
        return self.repo.save_shift(shift)

    def list_shifts(self, skip: int = 0, limit: int = 100) -> list[CashShift]:
        return self.repo.list_shifts(skip=skip, limit=limit)

    def create_sale(self, user: User, data: CashSaleCreate) -> CashTransaction:
        shift = self.current_shift()
        total, items = self._build_items(data.items)
        cash_amount, card_amount = self._normalize_payment(data.payment_method, data.cash_amount, data.card_amount, total)

        try:
            for item in data.items:
                self.inventory.reserve_stock(item.product_id, item.quantity)

            transaction = CashTransaction(
                shift_id=shift.id,
                seller_id=user.id,
                operation_type=CashOperationType.SALE,
                payment_method=data.payment_method,
                total_amount=total,
                cash_amount=cash_amount,
                card_amount=card_amount,
                receipt_number=self._receipt_number(shift.id),
                comment=data.comment,
                items=items,
            )
            self.repo.add_transaction(transaction)
            for item in data.items:
                self.inventory.commit_reserved(item.product_id, item.quantity)
            shift.expected_cash += cash_amount
            self.db.add(shift)
            self.db.commit()
            self.db.refresh(transaction)
            return transaction
        except Exception:
            self.db.rollback()
            raise

    def create_refund(self, user: User, data: CashSaleCreate) -> CashTransaction:
        shift = self.current_shift()
        total, items = self._build_items(data.items)
        cash_amount, card_amount = self._normalize_payment(data.payment_method, data.cash_amount, data.card_amount, total)

        try:
            transaction = CashTransaction(
                shift_id=shift.id,
                seller_id=user.id,
                operation_type=CashOperationType.REFUND,
                payment_method=data.payment_method,
                total_amount=total,
                cash_amount=cash_amount,
                card_amount=card_amount,
                receipt_number=self._receipt_number(shift.id),
                comment=data.comment,
                items=items,
            )
            self.repo.add_transaction(transaction)
            for item in data.items:
                inventory = self.inventory.repo.get_by_product_id(item.product_id, for_update=True)
                if not inventory:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Inventory for product {item.product_id} not found")
                inventory.quantity += item.quantity
                self.db.add(inventory)
            shift.expected_cash -= cash_amount
            self.db.add(shift)
            self.db.commit()
            self.db.refresh(transaction)
            return transaction
        except Exception:
            self.db.rollback()
            raise

    def list_transactions(self, shift_id: int, skip: int = 0, limit: int = 100) -> list[CashTransaction]:
        if not self.repo.get_shift(shift_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash shift not found")
        return self.repo.list_transactions(shift_id, skip=skip, limit=limit)

    def shift_summary(self, shift_id: int) -> CashShiftSummary:
        shift = self.repo.get_shift(shift_id)
        if not shift:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash shift not found")
        transactions = self.repo.list_transactions(shift_id, limit=1000)
        sales_total = sum((t.total_amount for t in transactions if t.operation_type == CashOperationType.SALE), Decimal("0"))
        refunds_total = sum((t.total_amount for t in transactions if t.operation_type == CashOperationType.REFUND), Decimal("0"))
        cash_total = sum((t.cash_amount for t in transactions if t.operation_type == CashOperationType.SALE), Decimal("0"))
        cash_total -= sum((t.cash_amount for t in transactions if t.operation_type == CashOperationType.REFUND), Decimal("0"))
        card_total = sum((t.card_amount for t in transactions if t.operation_type == CashOperationType.SALE), Decimal("0"))
        card_total -= sum((t.card_amount for t in transactions if t.operation_type == CashOperationType.REFUND), Decimal("0"))
        return CashShiftSummary(
            shift=shift,
            sales_total=sales_total,
            refunds_total=refunds_total,
            cash_total=cash_total,
            card_total=card_total,
            receipt_count=len(transactions),
        )

    def _build_items(self, input_items) -> tuple[Decimal, list[CashTransactionItem]]:
        total = Decimal("0")
        result: list[CashTransactionItem] = []
        for item in input_items:
            product = self.products.get(item.product_id)
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {item.product_id} not found")
            total += product.price * item.quantity
            result.append(CashTransactionItem(product_id=product.id, quantity=item.quantity, unit_price=product.price))
        return total, result

    def _normalize_payment(self, method: PaymentMethod, cash: Decimal, card: Decimal, total: Decimal) -> tuple[Decimal, Decimal]:
        if method == PaymentMethod.CASH:
            cash, card = total, Decimal("0")
        elif method == PaymentMethod.CARD:
            cash, card = Decimal("0"), total
        elif cash + card != total:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mixed payment must equal receipt total")
        return cash, card

    def _receipt_number(self, shift_id: int) -> str:
        return f"R{shift_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}"
