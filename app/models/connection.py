from __future__ import annotations

import datetime
import ipaddress
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.models.user import User


class ConnectionTableModel(Base):
    """
    Represents a user connection log (login history).

    Relationships:
        user: Many-to-one -> User
    """

    __tablename__ = "connections"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)

    # _ip_address is exposed via ip_address property for validation
    _ip_address: Mapped[str] = mapped_column("ip_address", sa.String(45), nullable=False)

    connection_date: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime, default=lambda: datetime.datetime.now(datetime.UTC), nullable=False
    )
    user: Mapped["User"] = relationship(back_populates="connections")

    @property
    def ip_address(self) -> str:
        """Returns the stored IP address."""
        return self._ip_address

    @ip_address.setter
    def ip_address(self, value: str):
        """
        Validates and normalizes the IP address before setting.
        Raises ValueError if invalid.
        """
        try:
            # Normalize (e.g., compress IPv6, standard IPv4 format)
            self._ip_address = str(ipaddress.ip_address(value))
        except ValueError:
            raise ValueError(f"Invalid IP address: {value}")

    def __repr__(self) -> str:
        return f"<Connection(id={self.id}, user_id={self.user_id}, ip={self._ip_address}, date={self.connection_date})>"