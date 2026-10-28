from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_admin
from app.reviews.schemas import ProductRating, ReviewCreate, ReviewModerate, ReviewOut, ReviewUpdate
from app.reviews.service import ReviewService
from app.users.models import User, UserRole

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("/product/{product_id}", response_model=list[ReviewOut])
def list_product_reviews(
    product_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List approved reviews for a product."""
    return ReviewService(db).list_by_product(product_id, skip, limit)


@router.get("/product/{product_id}/rating", response_model=ProductRating)
def get_product_rating(product_id: int, db: Session = Depends(get_db)):
    return ReviewService(db).get_product_rating(product_id)


@router.post("/", response_model=ReviewOut, status_code=201)
def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ReviewService(db).create_review(user.id, data)


@router.patch("/{review_id}", response_model=ReviewOut)
def update_review(
    review_id: int,
    data: ReviewUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ReviewService(db).update_review(review_id, user.id, data)


@router.delete("/{review_id}", status_code=204)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    is_admin = user.role == UserRole.ADMIN
    ReviewService(db).delete_review(review_id, user.id, is_admin)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Admin moderation endpoints ---

@router.get("/admin/pending", response_model=list[ReviewOut], dependencies=[Depends(require_admin)])
def list_pending_reviews(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List reviews awaiting moderation."""
    return ReviewService(db).list_pending(skip, limit)


@router.patch("/admin/{review_id}/moderate", response_model=ReviewOut, dependencies=[Depends(require_admin)])
def moderate_review(
    review_id: int,
    data: ReviewModerate,
    db: Session = Depends(get_db),
):
    """Approve or reject a review."""
    return ReviewService(db).moderate_review(review_id, data)
