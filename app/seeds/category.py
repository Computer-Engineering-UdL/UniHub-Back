import uuid
from typing import List

from sqlalchemy.orm import Session

from app.domains.housing import HousingCategoryRepository
from app.models import HousingCategoryTableModel


def seed_housing_categories(db: Session) -> List[HousingCategoryTableModel]:
    """Populate database with housing categories."""

    category_repo = HousingCategoryRepository(db)

    categories = category_repo.get_all()
    if categories:
        print("  → Housing categories already exist, skipping...")
        return categories

    categories_data = [
        {"id": uuid.uuid4(), "name": "Room"},
        {"id": uuid.uuid4(), "name": "Flat"},
        {"id": uuid.uuid4(), "name": "Detached House"},
        {"id": uuid.uuid4(), "name": "Studio"},
        {"id": uuid.uuid4(), "name": "Loft"},
    ]

    for cat_data in categories_data:
        category = HousingCategoryTableModel(**cat_data)
        db.add(category)
        categories.append(category)

    db.flush()

    print(f"  → {len(categories)} housing categories added")

    return categories
