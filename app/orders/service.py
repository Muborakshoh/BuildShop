from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.inventory.service import InventoryService
from app.orders.models import Order, OrderItem, OrderStatus, OrderStatusHistory, VALID_TRANSITIONS
from app.orders.repository import OrderRepository
from app.orders.schemas import OrderCreate, OrderStatusUpdate
from app.products.repository import ProductRepository
from app.users.models import User, UserRole
from app.delivery.models import DeliveryZone


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.orders = OrderRepository(db)
        self.products = ProductRepository(db)
        self.inventory = InventoryService(db)

    def create_order(self, user: User, data: OrderCreate) -> Order:
        product_ids = [item.product_id for item in data.items]
        if len(product_ids) != len(set(product_ids)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate products in order")

        order_items: list[OrderItem] = []
        total = Decimal("0.00")
        try:
            for item in data.items:
                product = self.products.get(item.product_id)
                if not product:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {item.product_id} not found")
                if hasattr(product, 'is_active') and not product.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product '{product.name}' is not available"
                    )
                self.inventory.reserve_stock(item.product_id, item.quantity)
                total += product.price * item.quantity
                order_items.append(OrderItem(product_id=product.id, quantity=item.quantity, unit_price=product.price, product_name=product.name))

            # Calculate delivery price
            delivery_price = Decimal("0")
            if data.delivery_method == "delivery" and data.delivery_zone_id:
                zone = self.db.query(DeliveryZone).get(data.delivery_zone_id)
                if zone and zone.is_active:
                    if zone.min_order_for_free and total >= zone.min_order_for_free:
                        delivery_price = Decimal("0")
                    else:
                        delivery_price = zone.price

            saved_order = Order(
                user_id=user.id,
                delivery_method=data.delivery_method,
                delivery_address=data.delivery_address,
                delivery_zone_id=data.delivery_zone_id,
                delivery_price=delivery_price,
                payment_method=data.payment_method,
                phone=data.phone,
                comment=data.comment,
                total_amount=total + delivery_price,
                items=order_items,
            )
            self.db.add(saved_order)
            self.db.flush()

            # Log initial status
            history = OrderStatusHistory(
                order_id=saved_order.id,
                old_status=None,
                new_status=OrderStatus.CREATED.value,
                comment="Order created",
                changed_by=user.id,
            )
            self.orders.add_status_history(history)

            for item in data.items:
                self.inventory.commit_reserved(item.product_id, item.quantity)
            self.db.commit()
            self.db.refresh(saved_order)
            return saved_order
        except Exception:
            self.db.rollback()
            raise

    def list_user_orders(self, user: User, skip: int = 0, limit: int = 100) -> list[Order]:
        if user.role == UserRole.ADMIN:
            return self.orders.list_all(skip=skip, limit=limit)
        return self.orders.list_for_user(user.id, skip=skip, limit=limit)

    def get_order(self, order_id: int, user: User) -> Order:
        order = self.orders.get(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        if user.role != UserRole.ADMIN and order.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return order

    def update_status(self, order_id: int, data: OrderStatusUpdate, changed_by_id: int | None = None) -> Order:
        order = self.orders.get(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        old_status = order.status
        new_status = data.status

        # Validate transition
        allowed = VALID_TRANSITIONS.get(old_status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from {old_status.value} to {new_status.value}. Allowed: {[s.value for s in allowed]}",
            )

        # Restore stock on cancellation
        if new_status == OrderStatus.CANCELLED and old_status != OrderStatus.CANCELLED:
            for item in order.items:
                self.inventory.restore_sold_stock(item.product_id, item.quantity)

        order.status = new_status

        # Log status change
        history = OrderStatusHistory(
            order_id=order.id,
            old_status=old_status.value,
            new_status=new_status.value,
            comment=data.comment,
            changed_by=changed_by_id,
        )
        self.orders.add_status_history(history)

        return self.orders.update(order)
