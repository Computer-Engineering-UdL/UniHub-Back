import datetime
import os
import uuid

from sqlalchemy.orm import Session

from app.models import (
    HousingCategoryTableModel,
    HousingOfferTableModel,
    HousingPhotoTableModel,
    User,
)


def seed_housing_data(db: Session) -> None:
    """Populate database with example housing categories, offers, and photos."""

    user = db.query(User).first()
    if not user:
        print("No user found. Skipping housing seed.")
        return

    categories = db.query(HousingCategoryTableModel).all()
    if not categories:
        categories = [
            HousingCategoryTableModel(id=uuid.uuid4(), name="Room"),
            HousingCategoryTableModel(id=uuid.uuid4(), name="Flat"),
            HousingCategoryTableModel(id=uuid.uuid4(), name="Detached House"),
            HousingCategoryTableModel(id=uuid.uuid4(), name="Studio"),
            HousingCategoryTableModel(id=uuid.uuid4(), name="Loft"),
        ]
        db.add_all(categories)
        db.flush()
        print(f"* Housing categories added: {len(categories)}")
    else:
        print(f"* Housing categories already exist: {len(categories)}")

    offers_data = [
        {
            "title": "Cozy room in shared flat near university",
            "description": "Fully furnished room with balcony access. Great location close to metro.",
            "price": 450,
            "area": 18,
            "city": "Madrid",
            "address": "Calle de Serrano 25",
            "category": categories[0],
        },
        {
            "title": "Modern 2-bedroom flat with terrace",
            "description": "Spacious apartment perfect for students or couples. Includes Wi-Fi and air conditioning.",
            "price": 950,
            "area": 65,
            "city": "Barcelona",
            "address": "Passeig de Gracia 12",
            "category": categories[1],
        },
        {
            "title": "Quiet detached house with garden",
            "description": "3-bedroom house with private garden and parking. Pets allowed.",
            "price": 1500,
            "area": 120,
            "city": "Valencia",
            "address": "Calle Mayor 8",
            "category": categories[2],
        },
        {
            "title": "Sunny loft apartment in city center",
            "description": "Bright open-plan loft with modern furniture and excellent natural light.",
            "price": 1100,
            "area": 50,
            "city": "Sevilla",
            "address": "Avenida de la Constitución 45",
            "category": categories[4],
        },
        {
            "title": "Affordable studio near the beach",
            "description": "Compact studio ideal for one person, just 5 minutes from the sea.",
            "price": 600,
            "area": 28,
            "city": "Málaga",
            "address": "Calle Larios 30",
            "category": categories[3],
        },
        {
            "title": "Large family house with pool",
            "description": "Detached home with 4 bedrooms, private pool and garden in quiet neighborhood.",
            "price": 2100,
            "area": 180,
            "city": "Alicante",
            "address": "Carrer de la Mar 10",
            "category": categories[2],
        },
        {
            "title": "Modern flat with private parking",
            "description": "Renovated 3-bedroom flat near public transport and shopping centers.",
            "price": 1300,
            "area": 90,
            "city": "Zaragoza",
            "address": "Calle del Coso 14",
            "category": categories[1],
        },
        {
            "title": "Room in shared flat with students",
            "description": "Friendly student flat with shared kitchen and common living area.",
            "price": 400,
            "area": 15,
            "city": "Granada",
            "address": "Calle Recogidas 11",
            "category": categories[0],
        },
        {
            "title": "Stylish loft with panoramic views",
            "description": "Top-floor loft apartment with floor-to-ceiling windows and private terrace.",
            "price": 1450,
            "area": 70,
            "city": "Bilbao",
            "address": "Gran Vía de Don Diego López 50",
            "category": categories[4],
        },
        {
            "title": "Quiet studio near public library",
            "description": "Newly refurbished studio in calm residential area with excellent transport links.",
            "price": 520,
            "area": 25,
            "city": "Tarragona",
            "address": "Rambla Nova 32",
            "category": categories[3],
        },
    ]

    created_offers = []

    for i, data in enumerate(offers_data, start=1):
        existing = db.query(HousingOfferTableModel).filter_by(title=data["title"], city=data["city"]).first()
        if existing:
            continue

        offer = HousingOfferTableModel(
            id=uuid.uuid4(),
            title=data["title"],
            description=data["description"],
            price=data["price"],
            area=data["area"],
            offer_valid_until=datetime.date(2025, 12, 31),
            start_date=datetime.date(2025, 10, 17),
            city=data["city"],
            address=data["address"],
            user_id=user.id,
            category_id=data["category"].id,
            posted_date=datetime.datetime.now(datetime.UTC),
        )
        db.add(offer)
        created_offers.append((offer, i))

    db.flush()

    added_photos = 0
    for offer, index in created_offers:
        photo_dir = f"app/static_photos/offer{index}"
        if not os.path.isdir(photo_dir):
            continue

        photo_files = [f for f in os.listdir(photo_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

        for file_name in photo_files:
            photo = HousingPhotoTableModel(
                id=uuid.uuid4(),
                url=f"/static_photos/offer{index}/{file_name}",
                offer_id=offer.id,
            )
            db.add(photo)
            added_photos += 1

    db.flush()

    if created_offers:
        print(f"* Housing offers added: {len(created_offers)}")
        print(f"* Housing photos added: {added_photos}")
    else:
        print("* No new housing offers added (already exist).")

    total_offers = db.query(HousingOfferTableModel).count()
    print(f"> Total offers in DB: {total_offers}")
