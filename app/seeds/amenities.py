from typing import List

from sqlalchemy.orm import Session

from app.domains.housing import HousingAmenityRepository
from app.models import HousingCategoryTableModel


def seed_amenities(db: Session) -> List[HousingCategoryTableModel]:
    """Populate database with housing categories."""

    amenity_repo = HousingAmenityRepository(db)

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
            amenities.append(amenity_repo.create(amenity_data))

    db.flush()

    print(f"  → {len(amenities)} housing amenities added")

    return amenities
