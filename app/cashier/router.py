from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.cashier.models import CashShift, CashTransaction
from app.cashier.schemas import CashSaleCreate, CashShiftClose, CashShiftOpen, CashShiftRead, CashShiftSummary, CashTransactionRead
from app.cashier.service import CashierService
from app.core.dependencies import get_current_user, get_db, require_roles
from app.users.models import User, UserRole

from app.cashier.schemas import XReportOut, ZReportOut

cashier_roles = require_roles(UserRole.SELLER, UserRole.MANAGER, UserRole.ADMIN)
manager_roles = require_roles(UserRole.MANAGER, UserRole.ADMIN)

router = APIRouter(prefix="/api/cashier", tags=["cashier"])


@router.post("/shifts/open", response_model=CashShiftRead, status_code=status.HTTP_201_CREATED)
def open_shift(payload: CashShiftOpen, current_user: User = Depends(cashier_roles), db: Session = Depends(get_db)) -> CashShift:
    return CashierService(db).open_shift(current_user, payload)


@router.get("/shifts/current", response_model=CashShiftRead)
def current_shift(
    register_name: str | None = None,
    current_user: User = Depends(cashier_roles),
    db: Session = Depends(get_db),
) -> CashShift:
    return CashierService(db).current_shift(register_name, current_user)

@router.post("/shifts/{shift_id}/close", response_model=CashShiftRead)
def close_shift(
    shift_id: int,
    payload: CashShiftClose,
    current_user: User = Depends(cashier_roles),
    db: Session = Depends(get_db),
) -> CashShift:
    return CashierService(db).close_shift(shift_id, current_user, payload)


@router.get("/shifts", response_model=list[CashShiftRead])
def list_shifts(skip: int = 0, limit: int = 100, current_user: User = Depends(cashier_roles), db: Session = Depends(get_db)) -> list[CashShift]:
    return CashierService(db).list_shifts(skip=skip, limit=limit)


@router.get("/shifts/{shift_id}/summary", response_model=CashShiftSummary)
def shift_summary(shift_id: int, current_user: User = Depends(cashier_roles), db: Session = Depends(get_db)) -> CashShiftSummary:
    return CashierService(db).shift_summary(shift_id, current_user)


@router.get("/shifts/{shift_id}/transactions", response_model=list[CashTransactionRead])
def list_transactions(
    shift_id: int,
    skip: int = 0,
    limit: int = 100,
    _: User = Depends(manager_roles),
    db: Session = Depends(get_db),
) -> list[CashTransaction]:
    return CashierService(db).list_transactions(shift_id, skip=skip, limit=limit)


@router.post("/sales", response_model=CashTransactionRead, status_code=status.HTTP_201_CREATED)
def create_sale(payload: CashSaleCreate, current_user: User = Depends(cashier_roles), db: Session = Depends(get_db)) -> CashTransaction:
    return CashierService(db).create_sale(current_user, payload)

@router.get("/shifts/{shift_id}/x-report", response_model=XReportOut)
def x_report(
    shift_id: int,
    current_user: User = Depends(cashier_roles),
    db: Session = Depends(get_db),
) -> dict:
    """Generate intermediate X-report (shift remains open)."""
    return CashierService(db).x_report(shift_id, current_user)


@router.get("/shifts/{shift_id}/z-report", response_model=ZReportOut)
def z_report(
    shift_id: int,
    current_user: User = Depends(cashier_roles),
    db: Session = Depends(get_db),
) -> dict:
    """Generate final Z-report (shift must be closed)."""
    return CashierService(db).z_report(shift_id, current_user)

@router.post("/refunds", response_model=CashTransactionRead, status_code=status.HTTP_201_CREATED)
def create_refund(payload: CashSaleCreate, current_user: User = Depends(manager_roles), db: Session = Depends(get_db)) -> CashTransaction:
    return CashierService(db).create_refund(current_user, payload)
