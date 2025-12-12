import datetime
import uuid
from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.literals.item import ItemCondition, ItemStatus

if TYPE_CHECKING:
    from app.models.file_association import FileAssociation
    from app.models.item_category import ItemCategoryTableModel
    from app.models.user import User


class ItemTableModel(Base):
    """
    Represents a marketplace item.
    """

    __tablename__ = "item"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ----- FOREIGN KEYS -----
    seller_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("item_category.id"), nullable=False)

    # ----- REQUIRED FIELDS -----
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    price: Mapped[float] = mapped_column(sa.Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(sa.String(3), default="EUR")
    location: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    condition: Mapped[ItemCondition] = mapped_column(sa.String(20), default=ItemCondition.GOOD, nullable=False)
    status: Mapped[ItemStatus] = mapped_column(sa.String(20), default=ItemStatus.ACTIVE, nullable=False)
    posted_date: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False
    )

    updated_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime, default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC)
    )

    # ----- RELATIONSHIPS -----

    seller: Mapped["User"] = relationship(back_populates="items")

    category: Mapped["ItemCategoryTableModel"] = relationship("ItemCategoryTableModel", back_populates="items")

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
        primaryjoin="and_(ItemTableModel.id==foreign(FileAssociation.entity_id), FileAssociation.entity_type=='item')",
        cascade="all, delete-orphan",
        lazy="selectin",
        viewonly=True,
    )

    # ----- INDEXES -----
    __table_args__ = (
        Index("ix_item_search", "title", "description"),
        Index("ix_item_price", "price"),
        Index("ix_item_location", "location"),
        Index("ix_item_status", "status"),
    )

    @property
    def images(self):
        """Helper for return URLs images."""
        return [f.file_url for f in self.file_associations]

    @property
    def owner_name(self):
        return f"{self.seller.first_name} {self.seller.last_name}".strip()

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, title={self.title})>"
