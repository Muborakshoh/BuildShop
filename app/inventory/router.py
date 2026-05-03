from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_admin
from app.inventory.models import Inventory
from app.inventory.schemas import InventoryAdjust, InventoryRead, InventorySet
from app.inventory.service import InventoryService

router = APIRouter(prefix="/api/inventory", tags=["inventory"], dependencies=[Depends(require_admin)])


def inventory_response(inventory: Inventory) -> InventoryRead:
    return InventoryRead(
        id=inventory.id,
        product_id=inventory.product_id,
        quantity=inventory.quantity,
        reserved=inventory.reserved,
        available=inventory.quantity - inventory.reserved,
        updated_at=inventory.updated_at,
    )


@router.get("", response_model=list[InventoryRead])
def list_inventory(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[InventoryRead]:
    return [inventory_response(item) for item in InventoryService(db).list_inventory(skip=skip, limit=limit)]


@router.get("/{product_id}", response_model=InventoryRead)
def get_inventory(product_id: int, db: Session = Depends(get_db)) -> InventoryRead:
    return inventory_response(InventoryService(db).get_product_inventory(product_id))


@router.put("/{product_id}", response_model=InventoryRead)
def set_inventory(product_id: int, payload: InventorySet, db: Session = Depends(get_db)) -> InventoryRead:
    return inventory_response(InventoryService(db).set_stock(product_id, payload))


@router.post("/{product_id}/adjust", response_model=InventoryRead)
def adjust_inventory(product_id: int, payload: InventoryAdjust, db: Session = Depends(get_db)) -> InventoryRead:
    return inventory_response(InventoryService(db).adjust_stock(product_id, payload))

