"""Factory for generating sample housing offer payloads for testing."""

from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID


def sample_offer_payload(
    user_id: Optional[str] = None,
    category_id: Optional[str] = None,
    title: str = "Test Housing Offer",
    description: str = "This is a test housing offer description.",
    price: float = 500.0,
    area: float = 50.0,
    city: str = "Test City",
    address: str = "123 Test Street",
    offer_valid_until: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    deposit: Optional[float] = 0.0,
    num_rooms: Optional[int] = 1,
    num_bathrooms: Optional[int] = 1,
    gender_preference: Optional[str] = "any",
    status: str = "active",
    amenities: Optional[List[int]] = None,
    photo_ids: Optional[List[UUID]] = None,
    # New boolean fields
    furnished: bool = False,
    utilities_included: bool = False,
    internet_included: bool = False,
    # New optional fields
    floor: Optional[int] = None,
    floor_number: Optional[int] = None,
    distance_from_campus: Optional[str] = None,
    utilities_cost: Optional[float] = None,
    utilities_description: Optional[str] = None,
    contract_type: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> dict:
    """
    Generate a sample housing offer payload for testing.
    Returns:
        dict: Payload ready for POST /offers/
    """
    # Default dates if not provided
    if offer_valid_until is None:
        offer_valid_until = str((date.today() + timedelta(days=90)).isoformat())
    if start_date is None:
        start_date = str(date.today().isoformat())
    if end_date is None:
        end_date = None  # Optional field

    payload = {
        "category_id": category_id,
        "title": title,
        "description": description,
        "price": price,
        "area": area,
        "city": city,
        "address": address,
        "offer_valid_until": offer_valid_until,
        "start_date": start_date,
        "end_date": end_date,
        "deposit": deposit,
        "num_rooms": num_rooms,
        "num_bathrooms": num_bathrooms,
        "gender_preference": gender_preference,
        "status": status,
        # New boolean fields
        "furnished": furnished,
        "utilities_included": utilities_included,
        "internet_included": internet_included,
    }

    # Add user_id if provided (for direct API calls)
    if user_id is not None:
        payload["user_id"] = user_id

    # Add optional fields only if they have values
    if amenities is not None:
        payload["amenities"] = amenities

    if photo_ids is not None:
        payload["photo_ids"] = [str(pid) for pid in photo_ids]
    else:
        payload["photo_ids"] = []

    # Add new optional fields if provided
    if floor is not None:
        payload["floor"] = floor

    if floor_number is not None:
        payload["floor_number"] = floor_number

    if distance_from_campus is not None:
        payload["distance_from_campus"] = distance_from_campus

    if utilities_cost is not None:
        payload["utilities_cost"] = utilities_cost

    if utilities_description is not None:
        payload["utilities_description"] = utilities_description

    if contract_type is not None:
        payload["contract_type"] = contract_type

    if latitude is not None:
        payload["latitude"] = latitude

    if longitude is not None:
        payload["longitude"] = longitude

    return payload


def sample_offer_payload_minimal(
    user_id: str,
    category_id: str,
) -> dict:
    """
    Generate a minimal housing offer payload with only required fields.

    Args:
        user_id: UUID of the user creating the offer
        category_id: UUID of the housing category

    Returns:
        dict: Minimal payload ready for POST /offers/
    """
    return {
        "user_id": user_id,
        "category_id": category_id,
        "title": "Minimal Test Offer",
        "description": "Minimal description for testing.",
        "price": 400.0,
        "area": 30.0,
        "city": "Test City",
        "address": "1 Test Ave",
        "offer_valid_until": str((date.today() + timedelta(days=30)).isoformat()),
        "start_date": str(date.today().isoformat()),
        "end_date": None,
        "gender_preference": "any",
        "status": "active",
        "furnished": False,
        "utilities_included": False,
        "internet_included": False,
        "photo_ids": [],
    }


def sample_offer_payload_lleida(
    user_id: str,
    category_id: str,
) -> dict:
    """
    Generate a sample housing offer payload for Lleida with realistic data.

    Args:
        user_id: UUID of the user creating the offer
        category_id: UUID of the housing category

    Returns:
        dict: Lleida-specific payload ready for POST /offers/
    """
    return sample_offer_payload(
        user_id=user_id,
        category_id=category_id,
        title="Student Room in Lleida City Center",
        description="Cozy furnished room perfect for university students. Close to campus and all amenities.",
        price=380.0,
        area=14.0,
        city="Lleida",
        address="Carrer Major, 25007 Lleida",
        num_rooms=1,
        num_bathrooms=1,
        furnished=True,
        utilities_included=True,
        internet_included=True,
        floor=2,
        distance_from_campus="900m",
        contract_type="semester",
        latitude=41.6147,
        longitude=0.6267,
        amenities=[100, 105, 110, 112],  # Wi-Fi, Heating, Furnished, Desk
    )
