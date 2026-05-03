from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_admin
from app.orders.models import Order
from app.orders.schemas import OrderCreate, OrderRead, OrderStatusUpdate
from app.orders.service import OrderService
from app.users.models import User

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Order:
    return OrderService(db).create_order(current_user, payload)


@router.get("", response_model=list[OrderRead])
def list_orders(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Order]:
    return OrderService(db).list_user_orders(current_user, skip=skip, limit=limit)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Order:
    return OrderService(db).get_order(order_id, current_user)


@router.patch("/{order_id}/status", response_model=OrderRead, dependencies=[Depends(require_admin)])
def update_order_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db)) -> Order:
    return OrderService(db).update_status(order_id, payload)

