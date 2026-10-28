from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.reviews.models import ReviewStatus


class ReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(ge=1, le=5)
    text: str | None = Field(default=None, max_length=2000)


class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    text: str | None = Field(default=None, max_length=2000)


class ReviewModerate(BaseModel):
    status: ReviewStatus


class ReviewAuthor(BaseModel):
    id: int
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class ReviewOut(BaseModel):
    user_id: int
    id: int
    product_id: int
    rating: int
    text: str | None
    status: ReviewStatus
    created_at: datetime
    updated_at: datetime
    user: ReviewAuthor

    model_config = ConfigDict(from_attributes=True)


class ProductRating(BaseModel):
    product_id: int
    avg_rating: float
    review_count: int
