import datetime
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import Mapped, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.models import User
    from app.models.terms import TermsTableModel


class UserTermsAcceptanceTableModel(Base):
    __tablename__ = "user_terms_acceptance"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(sa.UUID, ForeignKey("user.id"), nullable=False)
    terms_id = Column(sa.UUID, ForeignKey("terms.id"), nullable=False)

    accepted_at = Column(sa.DateTime, nullable=False, default=datetime.datetime.now(datetime.UTC))

    user: Mapped["User"] = relationship("User", back_populates="accepted_terms")
    terms: Mapped["TermsTableModel"] = relationship("TermsTableModel")
