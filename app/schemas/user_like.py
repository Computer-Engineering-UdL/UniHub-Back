import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.literals.like_status import LikeStatus, LikeTargetType


class UserLikeBase(BaseModel):
    target_id: uuid.UUID = Field(..., description="UUID of the liked object")
    target_type: LikeTargetType = Field(..., description="Type of the liked object")


# Schema for creating a like (used in POST)
class UserLikeCreate(UserLikeBase):
    pass


# Schema for reading a like (used in GET responses)
class UserLikeRead(UserLikeBase):
    user_id: uuid.UUID
    updated_at: datetime.datetime = Field(..., description="Timestamp of the last like/unlike action")
    status: LikeStatus

    model_config = ConfigDict(from_attributes=True)

class UserLikeUpdate(BaseModel):
    """Schema for updating a like status."""
    status: LikeStatus = Field(..., description="New status for the like (active/inactive)")


__all__ = [
    "UserLikeBase",
    "UserLikeCreate",
    "UserLikeRead",
    "UserLikeUpdate",
]

