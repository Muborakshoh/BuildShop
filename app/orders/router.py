from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_admin
from app.orders.models import Order, OrderStatus
from app.orders.schemas import OrderCreate, OrderRead, OrderStatusUpdate, StatusHistoryRead
from app.orders.service import OrderService
from app.users.models import User, UserRole
from app.notifications.dispatcher import notify_new_order, notify_order_status_change

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Order:
    order = OrderService(db).create_order(current_user, payload)
    try:
        notify_new_order(db, order)
    except Exception:
        pass  # notifications are non-critical
    return order


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


@router.patch("/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Order:
    svc = OrderService(db)
    if current_user.role != UserRole.ADMIN:
        order = svc.get_order(order_id, current_user)
        if payload.status != OrderStatus.CANCELLED:
            raise HTTPException(status_code=403, detail="Only admins can change order status")
    order = svc.update_status(order_id, payload, changed_by_id=current_user.id)
    try:
        notify_order_status_change(db, order, payload.status.value, payload.comment)
    except Exception:
        pass
    return order


@router.get("/{order_id}/history", response_model=list[StatusHistoryRead])
def get_order_history(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = OrderService(db).get_order(order_id, current_user)
    return order.status_history
