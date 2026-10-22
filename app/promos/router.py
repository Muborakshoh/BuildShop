from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_admin
from app.promos.schemas import (
    PromoApplyRequest,
    PromoApplyResponse,
    PromoCodeCreate,
    PromoCodeOut,
    PromoCodeUpdate,
)
from app.promos.service import PromoService
from app.users.models import User

router = APIRouter(prefix="/api/promos", tags=["promos"])


# ── Public: apply promo code
@router.post("/apply", response_model=PromoApplyResponse)
def apply_promo(
    data: PromoApplyRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return PromoService(db).apply_promo(user.id, data)


# ── Admin: CRUD
@router.get("/", response_model=list[PromoCodeOut], dependencies=[Depends(require_admin)])
def list_promos(db: Session = Depends(get_db)):
    return PromoService(db).list_all()


@router.post("/", response_model=PromoCodeOut, status_code=201, dependencies=[Depends(require_admin)])
def create_promo(data: PromoCodeCreate, db: Session = Depends(get_db)):
    return PromoService(db).create_promo(data)


@router.patch("/{promo_id}", response_model=PromoCodeOut, dependencies=[Depends(require_admin)])
def update_promo(promo_id: int, data: PromoCodeUpdate, db: Session = Depends(get_db)):
    return PromoService(db).update_promo(promo_id, data)


@router.delete("/{promo_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_promo(promo_id: int, db: Session = Depends(get_db)):
    PromoService(db).delete_promo(promo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
