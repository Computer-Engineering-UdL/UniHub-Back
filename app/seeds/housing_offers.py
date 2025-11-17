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
            "furnished": True,
            "utilities_included": False,
            "internet_included": True,
            "floor": 3,
            "num_rooms": 1,
            "num_bathrooms": 1,
            "utilities_cost": 50,
            "contract_type": "monthly",
            "latitude": 40.4168,
            "longitude": -3.7038,
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
            "furnished": True,
            "utilities_included": True,
            "internet_included": True,
            "floor": 5,
            "num_rooms": 2,
            "num_bathrooms": 2,
            "contract_type": "semester",
            "latitude": 41.3851,
            "longitude": 2.1734,
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
            "furnished": True,
            "utilities_included": False,
            "internet_included": True,
            "num_rooms": 3,
            "num_bathrooms": 2,
            "utilities_cost": 150,
            "utilities_description": "Electricity, water, and gas not included",
            "contract_type": "annual",
            "latitude": 39.4699,
            "longitude": -0.3763,
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
            "furnished": True,
            "utilities_included": True,
            "internet_included": True,
            "floor": 7,
            "num_rooms": 1,
            "num_bathrooms": 1,
            "contract_type": "monthly",
            "latitude": 37.3886,
            "longitude": -5.9823,
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
            "furnished": True,
            "utilities_included": False,
            "internet_included": True,
            "floor": 2,
            "num_rooms": 1,
            "num_bathrooms": 1,
            "utilities_cost": 60,
            "distance_from_campus": "2 km",
            "contract_type": "semester",
            "latitude": 36.7213,
            "longitude": -4.4214,
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
            "furnished": False,
            "utilities_included": False,
            "internet_included": False,
            "num_rooms": 4,
            "num_bathrooms": 3,
            "utilities_cost": 200,
            "utilities_description": "Water, electricity, gas, and internet not included",
            "contract_type": "annual",
            "latitude": 38.3452,
            "longitude": -0.4810,
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
            "furnished": True,
            "utilities_included": True,
            "internet_included": True,
            "floor": 4,
            "num_rooms": 3,
            "num_bathrooms": 2,
            "contract_type": "annual",
            "latitude": 41.6488,
            "longitude": -0.8891,
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
            "furnished": True,
            "utilities_included": True,
            "internet_included": True,
            "floor": 2,
            "num_rooms": 1,
            "num_bathrooms": 1,
            "distance_from_campus": "500m",
            "contract_type": "semester",
            "latitude": 37.1773,
            "longitude": -3.5986,
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
            "furnished": True,
            "utilities_included": False,
            "internet_included": True,
            "floor": 10,
            "num_rooms": 2,
            "num_bathrooms": 1,
            "utilities_cost": 80,
            "contract_type": "monthly",
            "latitude": 43.2627,
            "longitude": -2.9253,
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
            "furnished": True,
            "utilities_included": True,
            "internet_included": True,
            "floor": 1,
            "num_rooms": 1,
            "num_bathrooms": 1,
            "distance_from_campus": "1.5 km",
            "contract_type": "semester",
            "latitude": 41.1189,
            "longitude": 1.2445,
        },
        # Lleida housing offers
        {
            "title": "Student room near University of Lleida",
            "description": (
                "Comfortable furnished room in shared apartment, perfect for university students. "
                "10 minutes walk to campus."
            ),
            "price": 350,
            "area": 12,
            "city": "Lleida",
            "address": "Carrer de Jaume II, 25001 Lleida",
            "category_id": categories[0].id,
            "amenity_codes": [100, 105, 110, 112, 106],
            "furnished": True,
            "utilities_included": True,
            "internet_included": True,
            "floor": 2,
            "num_rooms": 1,
            "num_bathrooms": 1,
            "distance_from_campus": "800m",
            "contract_type": "semester",
            "latitude": 41.6175,
            "longitude": 0.6200,
        },
        {
            "title": "Modern flat in Lleida city center",
            "description": (
                "Beautiful 2-bedroom apartment with balcony in the heart of Lleida. Close to shops and restaurants."
            ),
            "price": 750,
            "area": 55,
            "city": "Lleida",
            "address": "Carrer Major, 25007 Lleida",
            "category_id": categories[1].id,
            "amenity_codes": [100, 104, 105, 106, 108, 115],
            "furnished": True,
            "utilities_included": False,
            "internet_included": True,
            "floor": 3,
            "num_rooms": 2,
            "num_bathrooms": 1,
            "utilities_cost": 70,
            "utilities_description": "Gas and electricity not included",
            "contract_type": "annual",
            "latitude": 41.6147,
            "longitude": 0.6267,
        },
        {
            "title": "Spacious room with private bathroom",
            "description": "Large room in a 4-bedroom shared flat near Parc de la Mitjana. Private bathroom included.",
            "price": 420,
            "area": 16,
            "city": "Lleida",
            "address": "Avinguda de Prat de la Riba, 25004 Lleida",
            "category_id": categories[0].id,
            "amenity_codes": [100, 105, 107, 110, 112],
            "furnished": True,
            "utilities_included": True,
            "internet_included": True,
            "floor": 1,
            "num_rooms": 1,
            "num_bathrooms": 1,
            "distance_from_campus": "1.2 km",
            "contract_type": "semester",
            "latitude": 41.6089,
            "longitude": 0.6145,
        },
        {
            "title": "Cozy studio near La Seu Vella",
            "description": "Charming studio apartment with views of the old cathedral. Ideal for one person.",
            "price": 480,
            "area": 22,
            "city": "Lleida",
            "address": "Carrer de Sant Martí, 25002 Lleida",
            "category_id": categories[3].id,
            "amenity_codes": [100, 105, 110],
            "furnished": True,
            "utilities_included": True,
            "internet_included": True,
            "floor": 4,
            "num_rooms": 1,
            "num_bathrooms": 1,
            "distance_from_campus": "1.8 km",
            "contract_type": "monthly",
            "latitude": 41.6142,
            "longitude": 0.6252,
        },
        {
            "title": "3-bedroom flat near Hospital Arnau",
            "description": "Spacious apartment perfect for families or students sharing. Well-connected area.",
            "price": 850,
            "area": 75,
            "city": "Lleida",
            "address": "Avinguda Alcalde Rovira Roure, 25198 Lleida",
            "category_id": categories[1].id,
            "amenity_codes": [100, 101, 102, 105, 106, 115],
            "furnished": False,
            "utilities_included": False,
            "internet_included": False,
            "floor": 5,
            "num_rooms": 3,
            "num_bathrooms": 2,
            "utilities_cost": 100,
            "utilities_description": "All utilities separate (approx. 100€/month)",
            "contract_type": "annual",
            "latitude": 41.6234,
            "longitude": 0.6089,
        },
        {
            "title": "Bright room in student residence",
            "description": "Furnished room in modern student building with study areas and gym. All services included.",
            "price": 550,
            "area": 14,
            "city": "Lleida",
            "address": "Carrer de Vallcalent, 25006 Lleida",
            "category_id": categories[0].id,
            "amenity_codes": [100, 105, 110, 112, 114, 115, 116],
            "furnished": True,
            "utilities_included": True,
            "internet_included": True,
            "floor": 6,
            "num_rooms": 1,
            "num_bathrooms": 1,
            "distance_from_campus": "600m",
            "contract_type": "semester",
            "latitude": 41.6198,
            "longitude": 0.6311,
        },
        {
            "title": "Detached house with garden in Lleida",
            "description": "Beautiful 4-bedroom house with private garden and parking. Quiet residential area.",
            "price": 1400,
            "area": 140,
            "city": "Lleida",
            "address": "Carrer de les Magnòlies, 25008 Lleida",
            "category_id": categories[2].id,
            "amenity_codes": [100, 101, 102, 103, 105, 109],
            "furnished": False,
            "utilities_included": False,
            "internet_included": False,
            "num_rooms": 4,
            "num_bathrooms": 3,
            "utilities_cost": 180,
            "utilities_description": "Water, electricity, gas separate",
            "contract_type": "annual",
            "latitude": 41.6256,
            "longitude": 0.6423,
        },
        {
            "title": "Affordable room for international students",
            "description": "Welcoming shared flat with multicultural environment. Close to bus station and university.",
            "price": 320,
            "area": 11,
            "city": "Lleida",
            "address": "Carrer d'Anselm Clavé, 25007 Lleida",
            "category_id": categories[0].id,
            "amenity_codes": [100, 105, 106, 110, 112],
            "furnished": True,
            "utilities_included": True,
            "internet_included": True,
            "floor": 3,
            "num_rooms": 1,
            "num_bathrooms": 1,
            "distance_from_campus": "1 km",
            "contract_type": "semester",
            "latitude": 41.6163,
            "longitude": 0.6289,
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
        lleida_count = sum(1 for offer in created_offers if offer.city == "Lleida")
        if lleida_count:
            print(f"  → {lleida_count} Lleida housing offers added")


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
