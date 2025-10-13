import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.literals.channels import ChannelRole, ChannelType

# ==========================================
# Channel Schemas
# ==========================================


class ChannelBase(BaseModel):
    """Main channel base schema."""

    name: str = Field(min_length=1, max_length=60)
    description: Optional[str] = Field(None, max_length=120)
    channel_type: ChannelType = Field(default="public")
    channel_logo: Optional[str] = None


class ChannelCreate(ChannelBase):
    """Schema for creating a new channel."""

    pass


class ChannelUpdate(BaseModel):
    """Schema for updating a channel (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=60)
    description: Optional[str] = Field(None, max_length=120)
    channel_type: ChannelType | None = None
    channel_logo: Optional[str] = None


class ChannelRead(ChannelBase):
    """Basic channel info without relationships."""

    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Channel Membership Schemas
# ==========================================


class MembershipRead(BaseModel):
    """Membership information."""

    user_id: uuid.UUID
    channel_id: uuid.UUID
    role: ChannelRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Channel Ban Schemas
# ==========================================


class BanRead(BaseModel):
    """Ban information."""

    user_id: uuid.UUID
    channel_id: uuid.UUID
    motive: str
    banned_at: datetime
    banned_by: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class UnbanRead(BaseModel):
    """Unban information."""

    user_id: uuid.UUID
    channel_id: uuid.UUID
    motive: str
    unbanned_at: datetime
    unbanned_by: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
