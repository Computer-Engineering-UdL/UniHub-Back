from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.domains.item.item_service import ItemService
from app.literals.item import ItemCondition, ItemSort
from app.models.user import User
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate, PagedItemsResult

router = APIRouter()


@router.get("/", response_model=PagedItemsResult)
def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    # Query param para recibir lista de IDs: ?category_ids=uuid1&category_ids=uuid2
    category_ids: Optional[List[UUID]] = Query(None),
    conditions: Optional[List[ItemCondition]] = Query(None),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    location: Optional[str] = None,
    sort: ItemSort = ItemSort.NEWEST,
    db: Session = Depends(get_db),
):
    """List items. Public endpoint."""
    service = ItemService(db)
    return service.get_items_paged(
        page=page,
        page_size=page_size,
        search=search,
        category_ids=category_ids,
        conditions=conditions,
        min_price=min_price,
        max_price=max_price,
        location=location,
        sort=sort,
    )


@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(
    item_in: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create item. Requires Auth."""
    service = ItemService(db)
    return service.create_item(current_user, item_in)


@router.get("/{item_id}", response_model=ItemRead)
def get_item_detail(
    item_id: UUID,
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    return service.get_item_detail(item_id)


@router.patch("/{item_id}", response_model=ItemRead)
def update_item(
    item_id: UUID,
    item_in: ItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    return service.update_item(item_id, current_user, item_in)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ItemService(db)
    service.delete_item(item_id, current_user)
