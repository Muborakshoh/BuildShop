from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.reviews.models import Review
from app.reviews.repository import ReviewRepository
from app.reviews.schemas import ReviewCreate, ReviewUpdate


class ReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReviewRepository(db)

    def list_by_product(self, product_id: int, skip: int = 0, limit: int = 50) -> list[Review]:
        return self.repo.list_by_product(product_id, skip, limit)

    def get_product_rating(self, product_id: int) -> dict:
        avg = self.repo.avg_rating_by_product(product_id)
        count = self.repo.count_by_product(product_id)
        return {"product_id": product_id, "avg_rating": avg or 0, "review_count": count}

    def get_bulk_ratings(self, product_ids: list[int]) -> dict[int, dict]:
        return self.repo.avg_ratings_bulk(product_ids)

    def create_review(self, user_id: int, data: ReviewCreate) -> Review:
        existing = self.repo.get_by_user_and_product(user_id, data.product_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already reviewed this product",
            )
        review = Review(
            user_id=user_id,
            product_id=data.product_id,
            rating=data.rating,
            text=data.text,
        )
        self.repo.create(review)
        self.db.commit()
        return review

    def update_review(self, review_id: int, user_id: int, data: ReviewUpdate) -> Review:
        review = self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        if review.user_id != user_id:
            raise HTTPException(status_code=403, detail="Cannot edit another user's review")
        if data.rating is not None:
            review.rating = data.rating
        if data.text is not None:
            review.text = data.text
        self.db.commit()
        self.db.refresh(review)
        return review

    def delete_review(self, review_id: int, user_id: int, is_admin: bool = False) -> None:
        review = self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        if review.user_id != user_id and not is_admin:
            raise HTTPException(status_code=403, detail="Cannot delete another user's review")
        self.repo.delete(review)
        self.db.commit()
