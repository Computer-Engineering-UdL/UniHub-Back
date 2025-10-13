import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import User


class Message(BaseModel):
    id: uuid.UUID = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(min_length=1, max_length=500)
    channel_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    is_edited: bool = Field(default=False)
    parent_message_id: Optional[str] = None

    user: Optional["User"] = None

    model_config = ConfigDict(from_attributes=True)
