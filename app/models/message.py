import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core import Base


class Message(Base):
    __tablename__ = "message"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    content = Column(sa.String(500), nullable=False)
    channel_id = Column(sa.UUID, ForeignKey("channel.id"), nullable=False)
    user_id = Column(sa.UUID, ForeignKey("user.id"), nullable=False)
    created_at = Column(sa.DateTime, nullable=False, default=datetime.now)
    updated_at = Column(sa.DateTime, nullable=True)
    is_edited = Column(sa.Boolean, nullable=False, default=False)
    parent_message_id = Column(sa.UUID, ForeignKey("message.id"), nullable=True)

    user = relationship("User", back_populates="messages")
    channel = relationship("Channel", back_populates="messages")

    parent_message = relationship("Message", remote_side=[id], backref="replies")
