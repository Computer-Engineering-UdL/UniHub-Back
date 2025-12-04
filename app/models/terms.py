import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy import Column

from app.core import Base


class TermsTableModel(Base):
    __tablename__ = "terms"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    version = Column(sa.String(20), unique=True, nullable=False)
    content = Column(sa.Text, nullable=False)
    created_at = Column(sa.DateTime, nullable=False, default=datetime.datetime.now(datetime.UTC))
