from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.orders.models import Order


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, order_id: int) -> Order | None:
        stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        return self.db.scalar(stmt)

    def list_for_user(self, user_id: int, skip: int = 0, limit: int = 100) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Order]:
        stmt = select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, order: Order) -> Order:
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def update(self, order: Order) -> Order:
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

