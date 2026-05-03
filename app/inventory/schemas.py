from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InventoryRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    reserved: int
    available: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventorySet(BaseModel):
    quantity: int = Field(ge=0)


class InventoryAdjust(BaseModel):
    delta: int = Field(ne=0)

