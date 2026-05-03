from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.inventory.service import InventoryService
from app.orders.models import Order, OrderItem, OrderStatus
from app.orders.repository import OrderRepository
from app.orders.schemas import OrderCreate, OrderStatusUpdate
from app.products.repository import ProductRepository
from app.users.models import User, UserRole


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
                self.inventory.reserve_stock(item.product_id, item.quantity)
                total += product.price * item.quantity
                order_items.append(OrderItem(product_id=product.id, quantity=item.quantity, unit_price=product.price))

            saved_order = Order(user_id=user.id, delivery_address=data.delivery_address, total_amount=total, items=order_items)
            self.db.add(saved_order)
            self.db.flush()
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

    def update_status(self, order_id: int, data: OrderStatusUpdate) -> Order:
        order = self.orders.get(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        if order.status == OrderStatus.CANCELLED and data.status != OrderStatus.CANCELLED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cancelled order cannot be reopened")
        order.status = data.status
        return self.orders.update(order)
