import math
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domains.file.file_association_service import FileAssociationService
from app.domains.item.item_repository import ItemRepository
from app.literals.item import ItemSort, ItemStatus
from app.literals.users import Role
from app.models.item import ItemTableModel
from app.models.item_category import ItemCategoryTableModel
from app.models.user import User
from app.schemas import FileAssociationCreate
from app.schemas.item import ItemCategoryRead, ItemCreate, ItemOwnerInfo, ItemRead, ItemUpdate, PagedItemsResult


class ItemService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ItemRepository(db)
        self.file_service = FileAssociationService(db)

    def _to_read_schema(self, item: ItemTableModel) -> ItemRead:
        owner_info = None
        if item.seller:
            owner_info = ItemOwnerInfo(
                id=item.seller.id,
                username=item.seller.username,
                full_name=f"{item.seller.first_name} {item.seller.last_name}",
                avatar_url=item.seller.avatar_url,
            )

        cat_read = ItemCategoryRead(id=item.category.id, name=item.category.name) if item.category else None
        item_dict = item.__dict__.copy()
        item_dict.pop("category", None)
        item_dict.pop("_sa_instance_state", None)

        return ItemRead(**item_dict, category=cat_read, image_urls=item.images, owner_details=owner_info)

    def create_item(self, user: User, item_in: ItemCreate) -> ItemRead:
        category = self.db.get(ItemCategoryTableModel, item_in.category_id)
        if not category:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Category ID")
        item_data = item_in.model_dump(exclude={"file_ids"})
        new_item = ItemTableModel(**item_data, seller_id=user.id)
        created_item = self.repo.create(new_item)

        if item_in.file_ids:
            associations_data = []
            for index, file_id in enumerate(item_in.file_ids):
                associations_data.append(
                    FileAssociationCreate(
                        file_id=file_id, entity_type="item", entity_id=created_item.id, order=index, category="gallery"
                    )
                )

            self.file_service.create_associations_bulk(associations=associations_data, current_user=user)
            self.db.refresh(created_item)

        return self.get_item_detail(created_item.id)

    def get_items_paged(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category_ids: Optional[List[uuid.UUID]] = None,
        conditions: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        location: Optional[str] = None,
        sort: ItemSort = ItemSort.NEWEST,
    ) -> PagedItemsResult:
        skip = (page - 1) * page_size
        items, total = self.repo.get_all(
            skip=skip,
            limit=page_size,
            search=search,
            category_ids=category_ids,
            conditions=conditions,
            min_price=min_price,
            max_price=max_price,
            location=location,
            sort=sort,
        )

        item_schemas = [self._to_read_schema(item) for item in items]
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0

        return PagedItemsResult(items=item_schemas, total=total, page=page, size=page_size, pages=total_pages)

    def get_item_detail(self, item_id: uuid.UUID) -> ItemRead:
        item = self.repo.get_by_id(item_id)

        if not item or item.status == ItemStatus.INACTIVE:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")

        return self._to_read_schema(item)

    def update_item(self, item_id: uuid.UUID, user: User, item_in: ItemUpdate) -> ItemRead:
        item = self.repo.get_by_id(item_id)
        if not item or item.status == ItemStatus.INACTIVE:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")

        if item.seller_id != user.id and user.role != Role.ADMIN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized")

        update_data = item_in.model_dump(exclude_unset=True, exclude={"file_ids"})

        if "category_id" in update_data:
            if not self.db.get(ItemCategoryTableModel, update_data["category_id"]):
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Category ID")

        for field, value in update_data.items():
            setattr(item, field, value)
        if item_in.file_ids is not None:
            self.file_service.delete_associations_by_entity(entity_type="item", entity_id=item.id, current_user=user)
            if item_in.file_ids:
                associations_data = []
                for index, file_id in enumerate(item_in.file_ids):
                    associations_data.append(
                        FileAssociationCreate(
                            file_id=file_id, entity_type="item", entity_id=item.id, order=index, category="gallery"
                        )
                    )
                self.file_service.create_associations_bulk(associations_data, current_user=user)

        updated_item = self.repo.update(item)
        return self.get_item_detail(updated_item.id)

    def delete_item(self, item_id: uuid.UUID, user: User):
        item = self.repo.get_by_id(item_id)
        if not item or item.status == ItemStatus.INACTIVE:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")

        if item.seller_id != user.id and user.role != Role.ADMIN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized")

        item.status = ItemStatus.INACTIVE
        self.repo.update(item)
