from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.core.dependencies import get_current_user, get_db, require_admin
from app.orders.models import CartItem, Order, OrderStatus
from app.orders.schemas import (
    CartItemCreate,
    CartItemRead,
    OrderCreate,
    OrderRead,
    OrderStatusUpdate,
    StatusHistoryRead,
)
from app.orders.service import OrderService
from app.users.models import User, UserRole
from app.notifications.dispatcher import notify_new_order, notify_order_status_change

router = APIRouter(prefix="/api/orders", tags=["orders"])


# --- Cart endpoints (ДОЛЖНЫ БЫТЬ ДО /{order_id}) ---

from sqlalchemy.orm import joinedload  # добавить в импорты

@router.get("/cart/me", response_model=list[CartItemRead])
def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[CartItem]:
    items = db.query(CartItem).options(joinedload(CartItem.product)).filter(CartItem.user_id == current_user.id).all()
    # Заполняем product_name и product_price из relationship
    for item in items:
        if item.product:
            item.product_name = item.product.name
            item.product_price = item.product.price
    return items

@router.post("/cart/me", response_model=CartItemRead, status_code=status.HTTP_201_CREATED)
def add_to_cart(payload: CartItemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CartItem:
    existing = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == payload.product_id
    ).first()
    if existing:
        existing.quantity += payload.quantity
        db.commit()
        db.refresh(existing)
        return existing
    item = CartItem(user_id=current_user.id, product_id=payload.product_id, quantity=payload.quantity)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/cart/me/{product_id}", response_model=CartItemRead)
def update_cart_item(product_id: int, payload: CartItemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CartItem:
    item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == product_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    item.quantity = payload.quantity
    db.commit()
    db.refresh(item)
    return item


@router.delete("/cart/me/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(product_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == product_id
    ).first()
    if item:
        db.delete(item)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/cart/me", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Order endpoints ---

@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Order:
    order = OrderService(db).create_order(current_user, payload)
    try:
        notify_new_order(db, order)
    except Exception:
        pass
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
        if order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only cancel your own orders")
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
