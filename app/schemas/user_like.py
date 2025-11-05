import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class UserLikeBase(BaseModel):
    target_id: uuid.UUID = Field(..., description="UUID of the liked object")
    target_type: str = Field(..., min_length=1, max_length=50,
                             description="Type of the liked object (e.g. housing_offer)")


# Schema for creating a like (used in POST)
class UserLikeCreate(UserLikeBase):
    pass


# Schema for reading a like (used in GET responses)
class UserLikeRead(UserLikeBase):
    id: uuid.UUID
    user_id: uuid.UUID
    liked_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

__all__ = [
    "UserLikeBase",
    "UserLikeCreate",
    "UserLikeRead",
]

