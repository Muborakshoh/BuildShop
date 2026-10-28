from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.reviews.models import Review, ReviewStatus


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, review_id: int) -> Review | None:
        return self.db.query(Review).filter(Review.id == review_id).first()

    def get_by_user_and_product(self, user_id: int, product_id: int) -> Review | None:
        return self.db.query(Review).filter(
            Review.user_id == user_id, Review.product_id == product_id
        ).first()

    def list_by_product(self, product_id: int, skip: int = 0, limit: int = 50, status: ReviewStatus | None = ReviewStatus.APPROVED) -> list[Review]:
        query = (
            self.db.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.product_id == product_id)
        )
        if status:
            query = query.filter(Review.status == status)
        return (
            query.order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_pending(self, skip: int = 0, limit: int = 50) -> list[Review]:
        return (
            self.db.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.status == ReviewStatus.PENDING)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_product(self, product_id: int, status: ReviewStatus | None = ReviewStatus.APPROVED) -> int:
        query = self.db.query(func.count(Review.id)).filter(Review.product_id == product_id)
        if status:
            query = query.filter(Review.status == status)
        return query.scalar() or 0

    def avg_rating_by_product(self, product_id: int) -> float | None:
        result = self.db.query(func.avg(Review.rating)).filter(
            Review.product_id == product_id,
            Review.status == ReviewStatus.APPROVED,
        ).scalar()
        return round(float(result), 1) if result else None

    def avg_ratings_bulk(self, product_ids: list[int]) -> dict[int, dict]:
        rows = (
            self.db.query(
                Review.product_id,
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("cnt"),
            )
            .filter(Review.product_id.in_(product_ids))
            .filter(Review.status == ReviewStatus.APPROVED)
            .group_by(Review.product_id)
            .all()
        )
        return {
            row.product_id: {"avg_rating": round(float(row.avg_rating), 1), "review_count": row.cnt}
            for row in rows
        }

    def create(self, review: Review) -> Review:
        self.db.add(review)
        self.db.flush()
        self.db.refresh(review)
        return review

    def delete(self, review: Review) -> None:
        self.db.delete(review)
        self.db.flush()
