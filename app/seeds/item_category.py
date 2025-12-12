from sqlalchemy.orm import Session

from app.models.item_category import ItemCategoryTableModel


def seed_item_categories(db: Session):
    """Pre-populate marketplace categories."""
    categories = ["Electronics", "Books", "Clothing", "Furniture", "Sports", "Music", "Other"]

    for name in categories:
        exists = db.query(ItemCategoryTableModel).filter_by(name=name).first()
        if not exists:
            db.add(ItemCategoryTableModel(name=name))

    db.commit()
