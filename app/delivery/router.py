from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_admin
from app.delivery.models import DeliveryZone
from app.delivery.schemas import (
    DeliveryCalcRequest,
    DeliveryCalcResponse,
    DeliveryZoneCreate,
    DeliveryZoneRead,
    DeliveryZoneUpdate,
)

router = APIRouter(prefix="/api/delivery", tags=["delivery"])


@router.get("/zones", response_model=list[DeliveryZoneRead])
def list_zones(db: Session = Depends(get_db)):
    """List active delivery zones (public)."""
    return db.query(DeliveryZone).filter(DeliveryZone.is_active == True).order_by(DeliveryZone.sort_order).all()


@router.get("/zones/all", response_model=list[DeliveryZoneRead])
def list_all_zones(db: Session = Depends(get_db), _=Depends(require_admin)):
    """List all zones including inactive (admin only)."""
    return db.query(DeliveryZone).order_by(DeliveryZone.sort_order).all()


@router.post("/zones", response_model=DeliveryZoneRead, status_code=status.HTTP_201_CREATED)
def create_zone(payload: DeliveryZoneCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    zone = DeliveryZone(**payload.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.patch("/zones/{zone_id}", response_model=DeliveryZoneRead)
def update_zone(zone_id: int, payload: DeliveryZoneUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    zone = db.query(DeliveryZone).get(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(zone, k, v)
    db.commit()
    db.refresh(zone)
    return zone


@router.delete("/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(zone_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    zone = db.query(DeliveryZone).get(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    db.delete(zone)
    db.commit()


@router.post("/calculate", response_model=DeliveryCalcResponse)
def calculate_delivery(payload: DeliveryCalcRequest, db: Session = Depends(get_db)):
    """Calculate delivery cost for a given zone and order total."""
    zone = db.query(DeliveryZone).get(payload.zone_id)
    if not zone or not zone.is_active:
        raise HTTPException(status_code=404, detail="Zone not found")

    is_free = False
    price = zone.price
    if zone.min_order_for_free and payload.order_total >= zone.min_order_for_free:
        is_free = True
        price = Decimal("0")

    return DeliveryCalcResponse(
        zone_name=zone.name,
        delivery_price=price,
        is_free=is_free,
        estimated_days=zone.estimated_days,
    )
