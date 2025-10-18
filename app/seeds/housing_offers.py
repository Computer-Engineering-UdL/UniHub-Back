import datetime
import os
import uuid

from sqlalchemy.orm import Session

from app.models import HousingCategoryTableModel, HousingOfferTableModel, HousingPhotoTableModel, User


def seed_housing_data(db: Session) -> None:
    """Populate database with example housing categories, offers and photos."""

    user = db.query(User).first()
    if not user:
        print("No user found. Skipping housing seed.")
        return

    existing_categories = db.query(HousingCategoryTableModel).all()
    if not existing_categories:
        categories = [
            HousingCategoryTableModel(id=uuid.uuid4(), name="Room"),
            HousingCategoryTableModel(id=uuid.uuid4(), name="Flat"),
            HousingCategoryTableModel(id=uuid.uuid4(), name="Detached House"),
        ]
        db.add_all(categories)
        db.flush()
    else:
        categories = existing_categories

    offers_data = [
        {
            "title": "Cozy room in shared flat near university",
            "description": "Fully furnished room with balcony access. Great location close to metro.",
            "price": 450,
            "area": 18,
            "offer_valid_until": datetime.datetime(2025, 12, 31).date(),
            "start_date": datetime.datetime(2025, 10, 17).date(),
            "city": "Madrid",
            "address": "Calle de Serrano 25",
            "category": categories[0],
        },
        {
            "title": "Modern 2-bedroom flat with terrace",
            "description": "Spacious apartment perfect for students or couples. Includes Wi-Fi and air conditioning.",
            "price": 950,
            "area": 65,
            "offer_valid_until": datetime.datetime(2025, 12, 31).date(),
            "start_date": datetime.datetime(2025, 10, 17).date(),
            "city": "Barcelona",
            "address": "Passeig de Gracia 12",
            "category": categories[1],
        },
        {
            "title": "Quiet detached house with garden",
            "description": "3-bedroom house with private garden and parking. Pets allowed.",
            "price": 1500,
            "area": 120,
            "offer_valid_until": datetime.datetime(2025, 12, 31).date(),
            "start_date": datetime.datetime(2025, 10, 17).date(),
            "city": "Valencia",
            "address": "Calle Mayor 8",
            "category": categories[2],
        },
    ]

    created_offers = []

    for i, offer_data in enumerate(offers_data, start=1):
        existing = (
            db.query(HousingOfferTableModel).filter_by(title=offer_data["title"], city=offer_data["city"]).first()
        )
        if existing:
            continue

        offer = HousingOfferTableModel(
            id=uuid.uuid4(),
            title=offer_data["title"],
            description=offer_data["description"],
            price=offer_data["price"],
            area=offer_data["area"],
            offer_valid_until=offer_data["offer_valid_until"],
            start_date=offer_data["start_date"],
            city=offer_data["city"],
            address=offer_data["address"],
            user_id=user.id,
            category_id=offer_data["category"].id,
            posted_date=datetime.datetime.now(datetime.UTC),
        )
        db.add(offer)
        created_offers.append((offer, i))

    db.flush()

    for offer, index in created_offers:
        photo_dir = f"app/static_photos/offer{index}"
        if not os.path.isdir(photo_dir):
            continue

        photo_files = [f for f in os.listdir(photo_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

        if not photo_files:
            continue

        for file_name in photo_files:
            photo_url = f"/static_photos/offer{index}/{file_name}"
            photo = HousingPhotoTableModel(
                id=uuid.uuid4(),
                url=photo_url,
                offer_id=offer.id,
            )
            db.add(photo)

    if created_offers:
        print(f"* Housing: {len(created_offers)} offers with photos")
