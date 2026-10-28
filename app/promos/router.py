from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_roles, require_admin
from app.promos.schemas import (
    PromoApplyRequest,
    PromoApplyResponse,
    PromoCodeCreate,
    PromoCodeOut,
    PromoCodeUpdate,
)
from app.promos.service import PromoService
from app.users.models import User,UserRole

router = APIRouter(prefix="/api/promos", tags=["promos"])
manager_roles = require_roles(UserRole.MANAGER, UserRole.ADMIN)

# ── Public: apply promo code
@router.post("/apply", response_model=PromoApplyResponse)
def apply_promo(
    data: PromoApplyRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return PromoService(db).apply_promo(user.id, data)


# ── Admin: CRUD
@router.get("/", response_model=list[PromoCodeOut], dependencies=[Depends(manager_roles)])
def list_promos(db: Session = Depends(get_db)):
    return PromoService(db).list_all()


@router.post("/", response_model=PromoCodeOut, status_code=201, dependencies=[Depends(manager_roles)])
def create_promo(data: PromoCodeCreate, db: Session = Depends(get_db)):
    return PromoService(db).create_promo(data)


@router.patch("/{promo_id}", response_model=PromoCodeOut, dependencies=[Depends(manager_roles)])
def update_promo(promo_id: int, data: PromoCodeUpdate, db: Session = Depends(get_db)):
    return PromoService(db).update_promo(promo_id, data)


@router.delete("/{promo_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_promo(promo_id: int, db: Session = Depends(get_db)):
    PromoService(db).delete_promo(promo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/my", response_model=list[PromoCodeOut])
def list_my_promos(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List personal promo codes for current user."""
    from app.promos.models import PromoCode
    return db.query(PromoCode).filter(
        PromoCode.user_id == user.id,
        PromoCode.is_active == True,
    ).all()
