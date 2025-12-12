from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.literals.item import ItemCondition, ItemStatus


class ItemCategoryRead(BaseModel):
    id: UUID
    name: str
    model_config = ConfigDict(from_attributes=True)


class ItemOwnerInfo(BaseModel):
    id: UUID
    username: str
    full_name: str
    avatar_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ItemBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str
    price: float
    currency: str = "EUR"
    location: str
    condition: ItemCondition = ItemCondition.GOOD

    @field_validator("price")
    def price_must_be_positive(cls, v):
        if v < 0:
            raise ValueError("Price must be non-negative")
        return v


class ItemCreate(ItemBase):
    category_id: UUID
    file_ids: List[UUID] = []


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    condition: Optional[ItemCondition] = None
    price: Optional[float] = None
    location: Optional[str] = None
    status: Optional[ItemStatus] = None
    file_ids: Optional[List[UUID]] = None


class ItemRead(ItemBase):
    id: UUID
    seller_id: UUID
    status: ItemStatus
    posted_date: datetime
    updated_at: Optional[datetime] = None
    category: ItemCategoryRead
    owner_details: Optional[ItemOwnerInfo] = None
    image_urls: List[str] = []
    model_config = ConfigDict(from_attributes=True)


class PagedItemsResult(BaseModel):
    items: List[ItemRead]
    total: int
    page: int
    size: int
    pages: int
