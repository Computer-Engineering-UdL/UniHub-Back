import datetime
import uuid
from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.literals.items import ItemCondition, ItemStatus

if TYPE_CHECKING:
    from app.models import FileAssociation
    from app.models.item_category import ItemCategoryTableModel
    from app.models.user import User


class ItemTableModel(Base):
    """
    Represents a marketplace item.

    Relationships:
        seller: Many-to-one -> User
        category: Many-to-one -> ItemCategoryTableModel
        file_associations: One-to-many -> FileAssociation (polymorphic: entity_type='item')
        liked_by_users: Many-to-many (polymorphic) -> User (via UserLike)

    Notes:
        - condition and status are literals defined in app.literals.items
        - posted_date is set automatically on creation
    """

    __tablename__ = "item"

    # ----- PRIMARY KEY -----
    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ----- FOREIGN KEYS -----
    seller_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("item_category.id"), nullable=False)

    # ----- REQUIRED FIELDS -----
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    price: Mapped[float] = mapped_column(sa.Numeric, nullable=False)
    condition: Mapped[ItemCondition] = mapped_column(sa.String(20), default="used", nullable=False)
    status: Mapped[ItemStatus] = mapped_column(sa.String(20), default="active", nullable=False)
    posted_date: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False
    )

    # ----- RELATIONSHIPS -----

    seller: Mapped["User"] = relationship(back_populates="items")

    category: Mapped["ItemCategoryTableModel"] = relationship(
        "ItemCategoryTableModel",
        back_populates="items"
    )

    liked_by_users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_like",
        primaryjoin="and_(ItemTableModel.id==UserLike.target_id, UserLike.target_type=='item')",
        secondaryjoin="User.id==UserLike.user_id",
        viewonly=True,
        back_populates=None,
        lazy="selectin",
    )

    file_associations: Mapped[List["FileAssociation"]] = relationship(
        "FileAssociation",
        primaryjoin="and_(ItemTableModel.id==foreign(FileAssociation.entity_id), "
                    "FileAssociation.entity_type=='item')",
        cascade="all, delete-orphan",
        lazy="selectin",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, category_id={self.category_id})>"