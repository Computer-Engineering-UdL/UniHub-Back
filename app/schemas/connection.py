from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConnectionBase(BaseModel):
    """Shared fields for create/update."""

    user_id: UUID
    ip_address: str = Field(
        description="IPv4 or IPv6 address from which the user connected."
    )

class ConnectionCreate(ConnectionBase):
    """Schema for recording a new connection entry."""
    pass

class ConnectionRead(ConnectionBase):
    """Full schema for reading a connection record."""

    id: UUID
    connection_date: datetime

    model_config = ConfigDict(from_attributes=True)

class ConnectionList(BaseModel):
    """Lightweight list entry."""

    id: UUID
    user_id: UUID
    ip_address: str
    connection_date: datetime

    model_config = ConfigDict(from_attributes=True)

__all__ = [
    "ConnectionBase",
    "ConnectionCreate",
    "ConnectionRead",
    "ConnectionList",
]

