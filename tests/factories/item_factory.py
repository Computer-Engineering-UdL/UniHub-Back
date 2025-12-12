from typing import List, Optional
from uuid import UUID

from app.literals.item import ItemCondition


def sample_item_payload(
    category_id: str,
    title: str = "MacBook Pro 2021",
    description: str = "Perfect condition, M1 Pro chip.",
    price: float = 1200.0,
    condition: str = ItemCondition.LIKE_NEW.value,
    location: str = "Barcelona",
    file_ids: Optional[List[UUID]] = None,
) -> dict:
    """
    Generate a sample marketplace item payload.
    """
    payload = {
        "title": title,
        "description": description,
        "category_id": category_id,
        "price": price,
        "currency": "EUR",
        "location": location,
        "condition": condition,
        "file_ids": [str(fid) for fid in file_ids] if file_ids else [],
    }
    return payload
