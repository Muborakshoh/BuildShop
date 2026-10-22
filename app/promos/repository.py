from sqlalchemy.orm import Session

from app.promos.models import PromoCode, PromoUsage


class PromoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, promo_id: int) -> PromoCode | None:
        return self.db.query(PromoCode).filter(PromoCode.id == promo_id).first()

    def get_by_code(self, code: str) -> PromoCode | None:
        return self.db.query(PromoCode).filter(PromoCode.code == code.upper()).first()

    def list_all(self) -> list[PromoCode]:
        return self.db.query(PromoCode).order_by(PromoCode.created_at.desc()).all()

    def create(self, promo: PromoCode) -> PromoCode:
        promo.code = promo.code.upper()
        self.db.add(promo)
        self.db.flush()
        self.db.refresh(promo)
        return promo

    def update(self, promo: PromoCode) -> PromoCode:
        self.db.flush()
        self.db.refresh(promo)
        return promo

    def delete(self, promo: PromoCode) -> None:
        self.db.delete(promo)
        self.db.flush()

    def user_used_promo(self, user_id: int, promo_id: int) -> bool:
        return self.db.query(PromoUsage).filter(
            PromoUsage.user_id == user_id, PromoUsage.promo_id == promo_id
        ).first() is not None

    def record_usage(self, usage: PromoUsage) -> PromoUsage:
        self.db.add(usage)
        self.db.flush()
        return usage
