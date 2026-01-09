from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey, Text
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.types import JSON

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class SystemSettings(Base):
    """
    Singleton table for storing all system configuration.
    Uses JSON columns for flexible storage of settings groups.
    """

    __tablename__ = "system_settings"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)

    system_settings = Column(JSON, nullable=False, default=dict)
    security_settings = Column(JSON, nullable=False, default=dict)
    content_settings = Column(JSON, nullable=False, default=dict)
    notification_settings = Column(JSON, nullable=False, default=dict)

    created_at = Column(sa.DateTime, nullable=False, default=datetime.datetime.now(datetime.UTC))
    updated_at = Column(
        sa.DateTime,
        nullable=False,
        default=datetime.datetime.now(datetime.UTC),
        onupdate=datetime.datetime.now(datetime.UTC),
    )


class SettingsAuditLog(Base):
    """Audit log for tracking configuration changes made by admins."""

    __tablename__ = "settings_audit_log"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    admin_id = Column(sa.UUID, ForeignKey("user.id"), nullable=False)
    changed_at = Column(sa.DateTime, nullable=False, default=datetime.datetime.now(datetime.UTC))
    ip_address = Column(sa.String(45), nullable=True)
    user_agent = Column(sa.String(255), nullable=True)

    changes = Column(JSON, nullable=False, default=dict)

    description = Column(Text, nullable=True)

    admin: Mapped["User"] = relationship("User", foreign_keys=[admin_id])
