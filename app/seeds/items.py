import datetime
import uuid
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from app.literals.item import ItemCondition, ItemStatus
from app.models import File, User
from app.models.file_association import FileAssociation
from app.models.item import ItemTableModel
from app.models.item_category import ItemCategoryTableModel


def seed_items(db: Session, users: List[User]) -> List[ItemTableModel]:
    """Create marketplace items with realistic data and static images."""

    existing_items = db.query(ItemTableModel).first()
    if existing_items:
        items = db.query(ItemTableModel).limit(10).all()
        print(f"* Items already seeded ({len(items)} items)")
        return items

    print("Seeding marketplace items...")

    electronics = db.query(ItemCategoryTableModel).filter_by(name="Electronics").first()
    furniture = db.query(ItemCategoryTableModel).filter_by(name="Furniture").first()
    sports = db.query(ItemCategoryTableModel).filter_by(name="Sports").first()
    other = db.query(ItemCategoryTableModel).filter_by(name="Other").first()

    if not electronics or not furniture or not sports or not other:
        print("ERROR: Item categories not found. Make sure to run seed_item_categories() first.")
        return []

    verified_users = [u for u in users if u.is_verified]
    if len(verified_users) < 3:
        print("ERROR: Not enough verified users found.")
        return []

    static_images_path = Path(__file__).parent.parent / "static_photos" / "second-hand"

    items_data = [
        {
            "title": 'MacBook Pro 13" 2020',
            "description": (
                "Well-maintained MacBook Pro with M1 chip, 8GB RAM, 256GB SSD. Used for two years for university work. "
                "Comes with original charger and protective case. Battery health at 87%. "
                "Perfect for students studying Computer Science or Engineering!"
            ),
            "price": 799.00,
            "currency": "EUR",
            "location": "Lleida, España",
            "condition": ItemCondition.GOOD,
            "category": electronics,
            "seller": verified_users[0],
            "image_folder": "MacbookPro",
        },
        {
            "title": "Mountain Bike - Giant Talon",
            "description": (
                'Giant Talon mountain bike in excellent condition. 27.5" wheels, aluminum frame, Shimano gears. '
                "Perfect for exploring the Pyrenees on weekends! Recently serviced with new brake pads. "
                "Ideal for students who love outdoor activities."
            ),
            "price": 450.00,
            "currency": "EUR",
            "location": "Lleida, España",
            "condition": ItemCondition.GOOD,
            "category": sports,
            "seller": verified_users[1],
            "image_folder": "Bike",
        },
        {
            "title": "Road Bike - Specialized Allez",
            "description": (
                "Specialized Allez road bike in great condition. "
                "Lightweight aluminum frame, carbon fork, Shimano 105 groupset. "
                "Perfect for students who want to stay fit and explore Catalonia! "
                "Includes bike lock and water bottle holder."
            ),
            "price": 520.00,
            "currency": "EUR",
            "location": "Lleida, España",
            "condition": ItemCondition.GOOD,
            "category": sports,
            "seller": verified_users[2],
            "image_folder": "Bike-2",
        },
        {
            "title": "Storage Cabinet / Bookshelf",
            "description": (
                "Solid wood storage cabinet, perfect for dorm rooms or small apartments. "
                "5 shelves providing ample space for books, decorations, and supplies. "
                "Some minor wear but very sturdy. Must pick up in Lleida. Great for organizing your study space!"
            ),
            "price": 45.00,
            "currency": "EUR",
            "location": "Lleida, España",
            "condition": ItemCondition.GOOD,
            "category": furniture,
            "seller": verified_users[0],
            "image_folder": "Cabinet",
        },
        {
            "title": "Large Minion Plush Toy",
            "description": (
                "Adorable large Minion plush toy, perfect for Despicable Me fans! "
                "Great condition, super soft and cuddly. "
                "Makes a fun decoration for your room or a nice gift. "
                "Approximately 50cm tall. Smoke-free home."
            ),
            "price": 15.00,
            "currency": "EUR",
            "location": "Lleida, España",
            "condition": ItemCondition.LIKE_NEW,
            "category": other,
            "seller": verified_users[1],
            "image_folder": "MinionPlush",
        },
    ]

    items = []
    admin_user = users[0]

    for item_data in items_data:
        image_folder_name = item_data.pop("image_folder")
        seller = item_data.pop("seller")
        category = item_data.pop("category")

        item = ItemTableModel(
            id=uuid.uuid4(),
            seller_id=seller.id,
            category_id=category.id,
            status=ItemStatus.ACTIVE,
            posted_date=datetime.datetime.now(datetime.UTC),
            updated_at=datetime.datetime.now(datetime.UTC),
            **item_data,
        )

        db.add(item)
        db.flush()

        image_folder_path = static_images_path / image_folder_name
        if image_folder_path.exists() and image_folder_path.is_dir():
            image_files = sorted(
                [
                    f
                    for f in image_folder_path.iterdir()
                    if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".webp"]
                ]
            )

            for order, image_path in enumerate(image_files):
                with open(image_path, "rb") as f:
                    image_data = f.read()

                ext = image_path.suffix.lower()
                content_type_map = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                }
                content_type = content_type_map.get(ext, "image/jpeg")

                file_record = File(
                    id=uuid.uuid4(),
                    filename=image_path.name,
                    content_type=content_type,
                    file_size=len(image_data),
                    uploaded_at=datetime.datetime.now(datetime.UTC),
                    is_public=True,
                    storage_type="database",
                    file_data=image_data,
                    uploader_id=admin_user.id,
                )

                db.add(file_record)
                db.flush()

                file_association = FileAssociation(
                    id=uuid.uuid4(),
                    file_id=file_record.id,
                    entity_type="item",
                    entity_id=item.id,
                    order=order,
                    created_at=datetime.datetime.now(datetime.UTC),
                )

                db.add(file_association)

            print(f"  - {item_data['title']}: {len(image_files)} images")
        else:
            print(f"WARNING: Image folder not found: {image_folder_path}")

        items.append(item)

    db.commit()

    print(f"* Created {len(items)} marketplace items with static images")
    return items
