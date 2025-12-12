import uuid
from typing import TYPE_CHECKING, List
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.models.item import ItemTableModel


class ItemCategoryTableModel(Base):
    """
    Represents a category for marketplace items (e.g., Electronics, Home & Garden, Education).

    Relationships:
        items: One-to-many -> ItemTableModel

    Notes:
        - A category must have a unique name.
        - A category cannot be deleted if items still reference it.
    """

    __tablename__ = "item_category"

    id: Mapped[UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ----- REQUIRED FIELDS -----
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False, unique=True)

    # ----- RELATIONSHIPS -----
    items: Mapped[List["ItemTableModel"]] = relationship(back_populates="category")
