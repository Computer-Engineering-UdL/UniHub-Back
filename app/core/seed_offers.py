import os
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.database import Base, engine
from app.models import HousingCategoryTableModel, HousingOfferTableModel, HousingPhotoTableModel, User


def seed_housing_data():
    """Populate database with example housing categories, offers and photos."""
    Base.metadata.create_all(bind=engine)
    db = Session(engine)

    try:
        # Get a user to assign offers to
        user = db.query(User).first()
        if not user:
            print("No user found. Please seed users first (run seed_database).")
            return

        # Create housing categories
        existing_categories = db.query(HousingCategoryTableModel).all()
        if not existing_categories:
            categories = [
                HousingCategoryTableModel(id=uuid.uuid4(), name="Room"),
                HousingCategoryTableModel(id=uuid.uuid4(), name="Flat"),
                HousingCategoryTableModel(id=uuid.uuid4(), name="Detached House"),
            ]
            db.add_all(categories)
            db.commit()
            print("Created housing categories.")
        else:
            categories = existing_categories
            print("Housing categories already exist, skipping creation.")

        # Example offers
        offers_data = [
            {
                "title": "Cozy room in shared flat near university",
                "description": "Fully furnished room with balcony access. Great location close to metro.",
                "price": 450,
                "area": 18,
                "offer_valid_until": datetime(2025, 12, 31).date(),
                "start_date": datetime(2025, 10, 17).date(),
                "city": "Madrid",
                "address": "Calle de Serrano 25",
                "category": categories[0],
            },
            {
                "title": "Modern 2-bedroom flat with terrace",
                "description": "Spacious apartment perfect for students or couples."
                               " Includes Wi-Fi and air conditioning.",
                "price": 950,
                "area": 65,
                "offer_valid_until": datetime(2025, 12, 31).date(),
                "start_date": datetime(2025, 10, 17).date(),
                "city": "Barcelona",
                "address": "Passeig de Gracia 12",
                "category": categories[1],
            },
            {
                "title": "Quiet detached house with garden",
                "description": "3-bedroom house with private garden and parking. Pets allowed.",
                "price": 1500,
                "area": 120,
                "offer_valid_until": datetime(2025, 12, 31).date(),
                "start_date": datetime(2025, 10, 17).date(),
                "city": "Valencia",
                "address": "Calle Mayor 8",
                "category": categories[2],
            },
        ]

        created_offers = []

        for i, offer_data in enumerate(offers_data, start=1):
            existing = (
                db.query(HousingOfferTableModel)
                .filter_by(title=offer_data["title"], city=offer_data["city"])
                .first()
            )
            if existing:
                print(f"Offer '{offer_data['title']}' already exists, skipping.")
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
                posted_date=datetime.utcnow(),
            )
            db.add(offer)
            created_offers.append((offer, i))

        db.commit()
        print(f"Created {len(created_offers)} housing offers.")

        # Add photos for each offer from local directories
        for offer, index in created_offers:
            photo_dir = f"app/static_photos/offer{index}"
            if not os.path.isdir(photo_dir):
                print(f"No photo directory found for: {photo_dir}")
                continue

            photo_files = [
                f for f in os.listdir(photo_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]

            if not photo_files:
                print(f"No photos found in: {photo_dir}")
                continue

            for file_name in photo_files:
                photo_url = f"/static_photos/offer{index}/{file_name}"
                photo = HousingPhotoTableModel(
                    id=uuid.uuid4(),
                    url=photo_url,
                    offer_id=offer.id,
                )
                db.add(photo)

            db.commit()
            print(f"Added {len(photo_files)} photos for offer: {offer.title}")

        print("Database seeded successfully with offers, categories, and photos!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding housing data: {e}")
    finally:
        db.close()
