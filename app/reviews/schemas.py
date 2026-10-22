from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(ge=1, le=5)
    text: str | None = Field(default=None, max_length=2000)


class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    text: str | None = Field(default=None, max_length=2000)


class ReviewAuthor(BaseModel):
    id: int
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class ReviewOut(BaseModel):
    id: int
    product_id: int
    rating: int
    text: str | None
    created_at: datetime
    updated_at: datetime
    user: ReviewAuthor

    model_config = ConfigDict(from_attributes=True)


class ProductRating(BaseModel):
    product_id: int
    avg_rating: float
    review_count: int
