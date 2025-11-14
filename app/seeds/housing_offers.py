import datetime
import os
import uuid
from typing import List

from sqlalchemy.orm import Session

from app.domains.file.file_association_repository import FileAssociationRepository
from app.domains.file.file_repository import FileRepository
from app.domains.housing import HousingAmenityRepository, HousingCategoryRepository, HousingOfferRepository
from app.models import HousingCategoryTableModel, HousingOfferTableModel, User
from app.schemas import FileAssociationCreate


def seed_housing_data(db: Session, users: List[User]) -> None:
    """Populate database with example housing categories, offers, and photos."""

    if not users:
        print("! No users found. Skipping housing seed.")
        return

    user = users[0]

    category_repo = HousingCategoryRepository(db)
    amenity_repo = HousingAmenityRepository(db)
    offer_repo = HousingOfferRepository(db)
    file_repo = FileRepository(db)
    file_assoc_repo = FileAssociationRepository(db)

    categories = category_repo.get_all()
    if not categories:
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

    amenities = amenity_repo.get_all()
    if not amenities:
        amenities_data = [
            {"code": 100, "name": "Wi-Fi"},
            {"code": 101, "name": "Parking"},
            {"code": 102, "name": "Washer"},
            {"code": 103, "name": "Dryer"},
            {"code": 104, "name": "Air Conditioning"},
            {"code": 105, "name": "Heating"},
            {"code": 106, "name": "Kitchen Access"},
            {"code": 107, "name": "Private Bathroom"},
            {"code": 108, "name": "Balcony"},
            {"code": 109, "name": "Garden Access"},
            {"code": 110, "name": "Furnished"},
            {"code": 111, "name": "TV"},
            {"code": 112, "name": "Desk"},
            {"code": 113, "name": "Pet Friendly"},
            {"code": 114, "name": "Bicycle Storage"},
            {"code": 115, "name": "Elevator"},
            {"code": 116, "name": "Security System"},
        ]
        for amenity_data in amenities_data:
            amenity_repo.create(amenity_data)
        amenities = amenity_repo.get_all()

    offers_data = [
        {
            "title": "Cozy room in shared flat near university",
            "description": "Fully furnished room with balcony access. Great location close to metro.",
            "price": 450,
            "area": 18,
            "city": "Madrid",
            "address": "Calle de Serrano 25",
            "category_id": categories[0].id,
            "amenity_codes": [100, 105, 110, 112],
        },
        {
            "title": "Modern 2-bedroom flat with terrace",
            "description": "Spacious apartment perfect for students or couples. Includes Wi-Fi and air conditioning.",
            "price": 950,
            "area": 65,
            "city": "Barcelona",
            "address": "Passeig de Gracia 12",
            "category_id": categories[1].id,
            "amenity_codes": [100, 104, 106, 102, 108],
        },
        {
            "title": "Quiet detached house with garden",
            "description": "3-bedroom house with private garden and parking. Pets allowed.",
            "price": 1500,
            "area": 120,
            "city": "Valencia",
            "address": "Calle Mayor 8",
            "category_id": categories[2].id,
            "amenity_codes": [100, 101, 109, 102, 105, 113],
        },
        {
            "title": "Sunny loft apartment in city center",
            "description": "Bright open-plan loft with modern furniture and excellent natural light.",
            "price": 1100,
            "area": 50,
            "city": "Sevilla",
            "address": "Avenida de la Constitución 45",
            "category_id": categories[4].id,
            "amenity_codes": [100, 105, 110],
        },
        {
            "title": "Affordable studio near the beach",
            "description": "Compact studio ideal for one person, just 5 minutes from the sea.",
            "price": 600,
            "area": 28,
            "city": "Málaga",
            "address": "Calle Larios 30",
            "category_id": categories[3].id,
            "amenity_codes": [100, 105],
        },
        {
            "title": "Large family house with pool",
            "description": "Detached home with 4 bedrooms, private pool and garden in quiet neighborhood.",
            "price": 2100,
            "area": 180,
            "city": "Alicante",
            "address": "Carrer de la Mar 10",
            "category_id": categories[2].id,
            "amenity_codes": [100, 101, 109, 102, 105],
        },
        {
            "title": "Modern flat with private parking",
            "description": "Renovated 3-bedroom flat near public transport and shopping centers.",
            "price": 1300,
            "area": 90,
            "city": "Zaragoza",
            "address": "Calle del Coso 14",
            "category_id": categories[1].id,
            "amenity_codes": [100, 101, 104, 106, 102],
        },
        {
            "title": "Room in shared flat with students",
            "description": "Friendly student flat with shared kitchen and common living area.",
            "price": 400,
            "area": 15,
            "city": "Granada",
            "address": "Calle Recogidas 11",
            "category_id": categories[0].id,
            "amenity_codes": [100, 105, 110, 112],
        },
        {
            "title": "Stylish loft with panoramic views",
            "description": "Top-floor loft apartment with floor-to-ceiling windows and private terrace.",
            "price": 1450,
            "area": 70,
            "city": "Bilbao",
            "address": "Gran Vía de Don Diego López 50",
            "category_id": categories[4].id,
            "amenity_codes": [100, 104, 108, 110],
        },
        {
            "title": "Quiet studio near public library",
            "description": "Newly refurbished studio in calm residential area with excellent transport links.",
            "price": 520,
            "area": 25,
            "city": "Tarragona",
            "address": "Rambla Nova 32",
            "category_id": categories[3].id,
            "amenity_codes": [100, 105],
        },
    ]

    created_offers = []
    added_photos = 0

    for i, data in enumerate(offers_data, start=1):
        existing = db.query(HousingOfferTableModel).filter_by(title=data["title"], city=data["city"]).first()
        if existing:
            continue

        amenity_codes = data.pop("amenity_codes", [])

        offer_data = {
            **data,
            "id": uuid.uuid4(),
            "offer_valid_until": datetime.date(2025, 12, 31),
            "start_date": datetime.date(2025, 10, 17),
            "user_id": user.id,
            "posted_date": datetime.datetime.now(datetime.UTC),
        }

        photo_ids = _process_offer_photos(db, i, user.id, file_repo)

        offer = offer_repo.create(
            offer_data,
            amenity_codes=amenity_codes,
            photo_ids=photo_ids,
        )

        if photo_ids:
            associations = [
                FileAssociationCreate(
                    file_id=file_id,
                    entity_type="housing_offer",
                    entity_id=offer.id,
                    order=idx,
                    category="photo",
                )
                for idx, file_id in enumerate(photo_ids)
            ]
            file_assoc_repo.bulk_create([assoc.model_dump() for assoc in associations])
            added_photos += len(photo_ids)

        created_offers.append(offer)

    db.commit()

    if created_offers:
        print(f"  → {len(created_offers)} housing offers added")
        print(f"  → {added_photos} photos added")


def _process_offer_photos(
    db: Session, offer_index: int, uploader_id: uuid.UUID, file_repo: FileRepository
) -> List[uuid.UUID]:
    """Process photos for an offer and return list of file IDs."""
    photo_dir = f"app/static_photos/offer{offer_index}"
    if not os.path.isdir(photo_dir):
        return []

    photo_files = [f for f in os.listdir(photo_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    file_ids = []

    for file_name in photo_files:
        file_path = os.path.join(photo_dir, file_name)
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()

            content_type = "image/jpeg" if file_name.lower().endswith((".jpg", ".jpeg")) else "image/png"

            file_data = {
                "id": uuid.uuid4(),
                "filename": file_name,
                "content_type": content_type,
                "file_data": file_content,
                "file_size": len(file_content),
                "uploader_id": uploader_id,
                "is_public": True,
                "storage_type": "database",
            }

            file_record = file_repo.create(file_data)
            file_ids.append(file_record.id)
        except Exception as e:
            print(f"! Error reading file {file_path}: {e}")
            continue

    return file_ids
