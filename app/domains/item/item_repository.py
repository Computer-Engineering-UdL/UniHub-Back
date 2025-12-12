import uuid
from typing import List, Optional, Tuple

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.literals.item import ItemCondition, ItemSort, ItemStatus
from app.models.item import ItemTableModel


class ItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, item: ItemTableModel) -> ItemTableModel:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_by_id(self, item_id: uuid.UUID) -> Optional[ItemTableModel]:
        stmt = (
            select(ItemTableModel)
            .where(ItemTableModel.id == item_id)
            .options(
                selectinload(ItemTableModel.category),
                selectinload(ItemTableModel.file_associations),
                selectinload(ItemTableModel.seller),
            )
        )
        return self.db.scalar(stmt)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        category_ids: Optional[List[uuid.UUID]] = None,
        conditions: Optional[List[ItemCondition]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        location: Optional[str] = None,
        sort: ItemSort = ItemSort.NEWEST,
    ) -> Tuple[List[ItemTableModel], int]:
        query = select(ItemTableModel).where(ItemTableModel.status == ItemStatus.ACTIVE)

        if search:
            search_filter = or_(
                ItemTableModel.title.ilike(f"%{search}%"), ItemTableModel.description.ilike(f"%{search}%")
            )
            query = query.where(search_filter)

        if category_ids:
            query = query.where(ItemTableModel.category_id.in_(category_ids))

        if conditions:
            query = query.where(ItemTableModel.condition.in_(conditions))

        if min_price is not None:
            query = query.where(ItemTableModel.price >= min_price)

        if max_price is not None:
            query = query.where(ItemTableModel.price <= max_price)

        if location:
            query = query.where(ItemTableModel.location.ilike(f"%{location}%"))

        count_stmt = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_stmt) or 0

        if sort == ItemSort.PRICE_ASC:
            query = query.order_by(asc(ItemTableModel.price))
        elif sort == ItemSort.PRICE_DESC:
            query = query.order_by(desc(ItemTableModel.price))
        else:
            query = query.order_by(desc(ItemTableModel.posted_date))

        query = (
            query.offset(skip)
            .limit(limit)
            .options(
                selectinload(ItemTableModel.category),
                selectinload(ItemTableModel.file_associations),
                selectinload(ItemTableModel.seller),
            )
        )

        items = list(self.db.scalars(query).all())
        return items, total

    def update(self, item: ItemTableModel) -> ItemTableModel:
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item: ItemTableModel) -> None:
        self.db.delete(item)
        self.db.commit()
