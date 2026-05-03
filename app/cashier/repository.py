from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.cashier.models import CashShift, CashShiftStatus, CashTransaction


class CashierRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_shift(self, shift_id: int) -> CashShift | None:
        return self.db.get(CashShift, shift_id)

    def get_open_shift(self, register_name: str | None = None) -> CashShift | None:
        stmt = select(CashShift).where(CashShift.status == CashShiftStatus.OPEN)
        if register_name:
            stmt = stmt.where(CashShift.register_name == register_name)
        return self.db.scalar(stmt.order_by(CashShift.opened_at.desc()))

    def list_shifts(self, skip: int = 0, limit: int = 100) -> list[CashShift]:
        stmt = select(CashShift).order_by(CashShift.opened_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def save_shift(self, shift: CashShift) -> CashShift:
        self.db.add(shift)
        self.db.commit()
        self.db.refresh(shift)
        return shift

    def add_transaction(self, transaction: CashTransaction) -> CashTransaction:
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def list_transactions(self, shift_id: int, skip: int = 0, limit: int = 100) -> list[CashTransaction]:
        stmt = (
            select(CashTransaction)
            .where(CashTransaction.shift_id == shift_id)
            .options(selectinload(CashTransaction.items))
            .order_by(CashTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
