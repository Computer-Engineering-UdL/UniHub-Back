from datetime import date


def sample_offer_payload(user_id: str = None, category_id: str = None, amenities: list[int] | None = None) -> dict:
    """Reusable housing offer payload."""
    payload = {
        "category_id": category_id,
        "title": "Test Apartment",
        "description": "A nice place",
        "price": 1000.0,
        "area": 50.0,
        "offer_valid_until": str(date.today()),
        "city": "Warsaw",
        "address": "Main Street 1",
        "start_date": str(date.today()),
        "end_date": str(date.today()),
        "deposit": 500.0,
        "num_rooms": 2,
        "num_bathrooms": 1,
        "gender_preference": None,
        "status": "active",
    }
    if user_id:
        payload["user_id"] = user_id
    if amenities is not None:
        payload["amenities"] = amenities
    return payload
