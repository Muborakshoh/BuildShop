from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.promos.models import PromoCode, PromoUsage
from app.promos.repository import PromoRepository
from app.promos.schemas import PromoApplyRequest, PromoCodeCreate, PromoCodeUpdate


class PromoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PromoRepository(db)

    def list_all(self) -> list[PromoCode]:
        return self.repo.list_all()

    def create_promo(self, data: PromoCodeCreate) -> PromoCode:
        if not data.discount_percent and not data.discount_amount:
            raise HTTPException(400, "Either discount_percent or discount_amount is required")
        existing = self.repo.get_by_code(data.code)
        if existing:
            raise HTTPException(409, f"Promo code '{data.code.upper()}' already exists")
        promo = PromoCode(**data.model_dump())
        self.repo.create(promo)
        self.db.commit()
        return promo

    def update_promo(self, promo_id: int, data: PromoCodeUpdate) -> PromoCode:
        promo = self.repo.get_by_id(promo_id)
        if not promo:
            raise HTTPException(404, "Promo code not found")
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(promo, key, val)
        self.repo.update(promo)
        self.db.commit()
        return promo

    def delete_promo(self, promo_id: int) -> None:
        promo = self.repo.get_by_id(promo_id)
        if not promo:
            raise HTTPException(404, "Promo code not found")
        self.repo.delete(promo)
        self.db.commit()

    def apply_promo(self, user_id: int, data: PromoApplyRequest) -> dict:
        promo = self.repo.get_by_code(data.code)
        if not promo:
            raise HTTPException(404, "Promo code not found")
        if not promo.is_active:
            raise HTTPException(400, "Promo code is inactive")
        now = datetime.now(timezone.utc)
        if promo.valid_from and now < promo.valid_from:
            raise HTTPException(400, "Promo code is not yet valid")
        if promo.valid_to and now > promo.valid_to:
            raise HTTPException(400, "Promo code has expired")
        if promo.usage_limit and promo.usage_count >= promo.usage_limit:
            raise HTTPException(400, "Promo code usage limit reached")
        if data.order_total < promo.min_order_amount:
            raise HTTPException(400, f"Minimum order amount: {promo.min_order_amount} TJS")
        if self.repo.user_used_promo(user_id, promo.id):
            raise HTTPException(400, "You have already used this promo code")

        # Calculate discount
        if promo.discount_percent:
            discount = data.order_total * promo.discount_percent / Decimal("100")
            if promo.max_discount and discount > promo.max_discount:
                discount = promo.max_discount
            desc = f"-{promo.discount_percent}%"
        else:
            discount = min(promo.discount_amount, data.order_total)
            desc = f"-{discount} TJS"

        discount = discount.quantize(Decimal("0.01"))
        new_total = (data.order_total - discount).quantize(Decimal("0.01"))

        return {
            "code": promo.code,
            "discount": discount,
            "new_total": new_total,
            "description": desc,
        }

    def confirm_usage(self, user_id: int, code: str, order_id: int, discount: Decimal) -> None:
        """Call after order is created to record usage and increment counter."""
        promo = self.repo.get_by_code(code)
        if not promo:
            return
        usage = PromoUsage(
            promo_id=promo.id,
            user_id=user_id,
            order_id=order_id,
            discount_applied=discount,
        )
        self.repo.record_usage(usage)
        promo.usage_count += 1
        self.db.flush()
