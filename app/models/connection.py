import datetime
import ipaddress
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.models import User

class ConnectionTableModel(Base):
    __tablename__ = "connections"

    id = Column(sa.UUID, primary_key=True)
    user_id = Column(sa.UUID, ForeignKey("user.id"), nullable=False)
    _ip_address = Column("ip_address", sa.String(45), nullable=False)
    connection_date = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

    user: Mapped["User"] = relationship(back_populates="connections")

    @property
    def ip_address(self):
        return self._ip_address

    @ip_address.setter
    def ip_address(self, value):
        # Validate + normalize (e.g., compress IPv6)
        try:
            self._ip_address = str(ipaddress.ip_address(value))
        except ValueError:
            raise ValueError(f"Invalid IP address: {value}")