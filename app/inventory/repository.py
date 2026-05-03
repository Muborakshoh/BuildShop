from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.inventory.models import Inventory


class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_product_id(self, product_id: int, for_update: bool = False) -> Inventory | None:
        stmt = select(Inventory).where(Inventory.product_id == product_id).options(selectinload(Inventory.product))
        if for_update:
            stmt = stmt.with_for_update()
        return self.db.scalar(stmt)

    def list(self, skip: int = 0, limit: int = 100) -> list[Inventory]:
        stmt = select(Inventory).options(selectinload(Inventory.product)).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def save(self, inventory: Inventory) -> Inventory:
        self.db.add(inventory)
        self.db.commit()
        self.db.refresh(inventory)
        return inventory

    def flush(self, inventory: Inventory) -> Inventory:
        self.db.add(inventory)
        self.db.flush()
        return inventory

