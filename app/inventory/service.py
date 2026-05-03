from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.inventory.models import Inventory
from app.inventory.repository import InventoryRepository
from app.inventory.schemas import InventoryAdjust, InventorySet
from app.products.repository import ProductRepository


class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InventoryRepository(db)
        self.products = ProductRepository(db)

    def list_inventory(self, skip: int = 0, limit: int = 100) -> list[Inventory]:
        return self.repo.list(skip=skip, limit=limit)

    def get_product_inventory(self, product_id: int) -> Inventory:
        inventory = self.repo.get_by_product_id(product_id)
        if not inventory:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found")
        return inventory

    def set_stock(self, product_id: int, data: InventorySet) -> Inventory:
        if not self.products.get(product_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        inventory = self.repo.get_by_product_id(product_id) or Inventory(product_id=product_id, reserved=0)
        if data.quantity < inventory.reserved:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity cannot be lower than reserved stock")
        inventory.quantity = data.quantity
        return self.repo.save(inventory)

    def adjust_stock(self, product_id: int, data: InventoryAdjust) -> Inventory:
        inventory = self.get_product_inventory(product_id)
        new_quantity = inventory.quantity + data.delta
        if new_quantity < inventory.reserved:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough stock")
        inventory.quantity = new_quantity
        return self.repo.save(inventory)

    def reserve_stock(self, product_id: int, quantity: int) -> Inventory:
        inventory = self.repo.get_by_product_id(product_id, for_update=True)
        if not inventory or inventory.quantity - inventory.reserved < quantity:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Not enough stock for product {product_id}")
        inventory.reserved += quantity
        return self.repo.flush(inventory)

    def release_reserved(self, product_id: int, quantity: int) -> Inventory:
        inventory = self.repo.get_by_product_id(product_id, for_update=True)
        if not inventory:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found")
        inventory.reserved = max(0, inventory.reserved - quantity)
        return self.repo.flush(inventory)

    def commit_reserved(self, product_id: int, quantity: int) -> Inventory:
        inventory = self.repo.get_by_product_id(product_id, for_update=True)
        if not inventory or inventory.reserved < quantity:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Reserved stock is missing for product {product_id}")
        inventory.reserved -= quantity
        inventory.quantity -= quantity
        return self.repo.flush(inventory)

