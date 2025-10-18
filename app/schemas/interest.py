import uuid
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class InterestRead(BaseModel):
    id: uuid.UUID
    name: str = Field(min_length=1, max_length=120)

    model_config = ConfigDict(from_attributes=True)


class InterestCategoryRead(BaseModel):
    id: uuid.UUID
    name: str = Field(min_length=1, max_length=120)
    interests: List[InterestRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UserInterestCreate(BaseModel):
    interest_id: uuid.UUID


__all__ = [
    "InterestRead",
    "InterestCategoryRead",
    "UserInterestCreate",
]
