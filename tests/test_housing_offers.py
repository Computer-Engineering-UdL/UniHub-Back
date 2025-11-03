import uuid
from datetime import date

from app.core.security import get_payload
from app.models import HousingCategoryTableModel, HousingOfferTableModel


def sample_offer_payload(user_id: str = None, category_id: str = None, amenities: list[int] | None = None) -> dict:
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
        "furnished": True,
        "utilities_included": True,
        "internet_included": False,
        "gender_preference": None,
        "status": "active",
    }
    if user_id:
        payload["user_id"] = user_id
    if amenities is not None:
        payload["amenities"] = amenities
    return payload

class TestHousingOfferEndpoints:

    def test_create_offer_success(self, client, user_token, auth_headers, db):
        user_data = get_payload(user_token)
        user_id = user_data["sub"]
        category = db.query(HousingCategoryTableModel).first()
        assert category is not None, "Category not found in test database!"

        payload = sample_offer_payload(user_id=user_id, category_id=str(category.id))
        resp = client.post("/offers/", json=payload, headers=auth_headers)
        assert resp.status_code == 201

    def test_create_offer_with_amenities(self, client, user_token, auth_headers, db):
        user_data = get_payload(user_token)
        user_id = user_data["sub"]
        category = db.query(HousingCategoryTableModel).first()
        assert category is not None, "Category not found in test database!"

        amenities = [100, 101, 102]
        payload = sample_offer_payload(user_id=user_id, category_id=str(category.id), amenities=amenities)
        resp = client.post("/offers/", json=payload, headers=auth_headers)
        print("Response JSON:", resp.json())
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data

    def test_create_offer_without_auth(self, client, db):
        category = db.query(HousingCategoryTableModel).first()
        assert category is not None

        payload = sample_offer_payload(category_id=str(category.id))
        resp = client.post("/offers/", json=payload)
        print("Response JSON:", resp.json())
        assert resp.status_code == 401

    def test_create_offer_empty_payload(self, client, auth_headers):
        payload = {}  # empty payload
        resp = client.post("/offers/", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_create_offer_wrong_type(self, client, auth_headers, db):
        """Send wrong type for 'price', expect 422 validation error."""
        # Pick valid user and category
        category = db.query(HousingCategoryTableModel).first()
        assert category is not None

        payload = sample_offer_payload(user_id="dummy", category_id=str(category.id))

        resp = client.post("/offers/", json=payload, headers=auth_headers)
        print("Response JSON:", resp.json())
        assert resp.status_code == 422

    def test_create_offer_end_before_start(self, client, user_token, auth_headers, db):
        """Set end_date before start_date, expect 422 validation error."""
        category = db.query(HousingCategoryTableModel).first()
        assert category is not None

        user_data = get_payload(user_token)
        user_id = user_data["sub"]

        payload = sample_offer_payload(user_id=user_id, category_id=str(category.id))
        payload["start_date"] = str(date.today())
        # End date before start date
        payload["end_date"] = str(date.today().replace(year=date.today().year - 1))

        resp = client.post("/offers/", json=payload, headers=auth_headers)
        print("Response JSON:", resp.json())
        assert resp.status_code == 422

    def test_get_offer_success(self, client, db):
        """Should return details of an existing offer."""
        # Select an existing offer from the test database
        offer = db.query(HousingOfferTableModel).first()
        assert offer is not None, "No offer found in the test database."

        resp = client.get(f"/offers/{offer.id}")
        print("Response JSON:", resp.json())

        assert resp.status_code == 200
        data = resp.json()

        # Verify key fields in the response
        assert data["id"] == str(offer.id)
        assert data["title"] == offer.title
        assert "category" in data
        assert "photos" in data
        assert isinstance(data["photos"], list)
        assert "photo_count" in data
        assert isinstance(data["photo_count"], int)

    def test_get_offer_not_found(self, client):
        """Should return 404 when the offer with given ID does not exist."""
        random_id = uuid.uuid4()
        resp = client.get(f"/offers/{random_id}")
        print("Response JSON:", resp.json())

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Offer not found."

    def test_get_offer_invalid_uuid(self, client):
        """Should return 422 when the provided ID is not a valid UUID."""
        resp = client.get("/offers/not-a-uuid")
        print("Response JSON:", resp.json())

        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_list_offers_success(self, client, db):
        """Should return a list of housing offers."""
        # Ensure there are offers in the database
        offers = db.query(HousingOfferTableModel).all()
        assert len(offers) > 0, "No offers found in the test database."

        resp = client.get("/offers/")
        print("Response JSON:", resp.json())

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Verify required fields in the first item
        sample = data[0]
        for field in ["id", "title", "price", "area", "status", "posted_date", "city"]:
            assert field in sample

    def test_list_offers_with_city_filter(self, client):
        """Should return only offers matching the given city name."""
        resp = client.get("/offers/?city=Madrid")
        print("Response JSON:", resp.json())

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # All offers should have 'Madrid' in city field (case-insensitive)
        for offer in data:
            assert "madrid" in offer["city"].lower()


    class TestListHousingOffers:
        def test_list_offers_with_category_filter(self, client, db):
            """Should return only offers that belong to the requested category (verify using DB)."""
            category = db.query(HousingCategoryTableModel).filter_by(name="Room").first()
            assert category is not None, "Category 'Room' not found in the test database."

            resp = client.get(f"/offers/?category_name={category.name}")
            print("Response JSON:", resp.json())

            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)

            returned_ids = {item["id"] for item in data}
            if returned_ids:
                db_offers = (
                    db.query(HousingOfferTableModel)
                    .filter(HousingOfferTableModel.id.in_([uuid.UUID(i) for i in returned_ids]))
                    .all()
                )
                db_ids = {str(o.id) for o in db_offers}
                assert returned_ids == db_ids, "Some returned offers were not found in DB."

                for o in db_offers:
                    assert str(o.category_id) == str(category.id)

    def test_list_offers_with_price_range(self, client):
        """Should return offers within the specified price range."""
        resp = client.get("/offers/?min_price=400&max_price=800")
        print("Response JSON:", resp.json())

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for offer in data:
            price = float(offer["price"])
            assert 400 <= price <= 800

    def test_list_offers_with_status_filter(self, client):
        """Should return only offers with the specified status."""
        resp = client.get("/offers/?status=active")
        print("Response JSON:", resp.json())

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for offer in data:
            assert offer["status"] == "active"

    def test_list_offers_with_pagination(self, client):
        """Should respect pagination parameters (skip and limit)."""
        resp = client.get("/offers/?skip=0&limit=1")
        print("Response JSON:", resp.json())

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) <= 1

    def test_list_offers_empty_result(self, client):
        """Should return an empty list when no offers match filters."""
        # Use a city name that does not exist in test data
        resp = client.get("/offers/?city=NonExistentCity")
        print("Response JSON:", resp.json())

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0


    def test_update_offer_as_owner(self, client, user_token, auth_headers, db):
        """Should allow the offer owner to update their own offer."""
        user_data = get_payload(user_token)
        user_id = user_data["sub"]

        category = db.query(HousingCategoryTableModel).first()
        assert category is not None, "Category not found in test database!"

        create_payload = sample_offer_payload(user_id=user_id, category_id=str(category.id))
        create_resp = client.post("/offers/", json=create_payload, headers=auth_headers)
        print("Create response JSON:", create_resp.json())
        assert create_resp.status_code == 201, "Offer creation failed during setup."
        offer_id = create_resp.json()["id"]

        update_payload = {"title": "Updated offer title"}
        patch_resp = client.patch(f"/offers/{offer_id}", json=update_payload, headers=auth_headers)
        print("Patch response JSON:", patch_resp.json())

        assert patch_resp.status_code == 200
        data = patch_resp.json()
        assert data["title"] == "Updated offer title"

        updated_offer = db.get(HousingOfferTableModel, uuid.UUID(offer_id))
        assert updated_offer is not None
        assert updated_offer.title == "Updated offer title"
        assert str(updated_offer.user_id) == user_id

    def test_update_offer_as_admin(self, client, admin_auth_headers, user_token, db):
        """Should allow an admin to update any user's offer."""
        user_data = get_payload(user_token)
        user_id = user_data["sub"]

        category = db.query(HousingCategoryTableModel).first()
        assert category is not None, "Category not found in test database!"

        create_payload = sample_offer_payload(user_id=user_id, category_id=str(category.id))
        create_resp = client.post("/offers/", json=create_payload, headers={"Authorization": f"Bearer {user_token}"})
        print("Create response JSON (user):", create_resp.json())
        assert create_resp.status_code == 201, "Offer creation failed during setup."
        offer_id = create_resp.json()["id"]

        update_payload = {"title": "Admin updated this offer"}
        patch_resp = client.patch(f"/offers/{offer_id}", json=update_payload, headers=admin_auth_headers)
        print("Patch response JSON (admin):", patch_resp.json())

        assert patch_resp.status_code == 200
        data = patch_resp.json()
        assert data["title"] == "Admin updated this offer"

        updated_offer = db.get(HousingOfferTableModel, uuid.UUID(offer_id))
        assert updated_offer is not None
        assert updated_offer.title == "Admin updated this offer"

    def test_update_offer_unauthorized_user(self, client, user_token, user2_token, db):
        """Should return 403 if a non-owner, non-admin tries to update an offer."""
        # user1 creates an offer
        user1_data = get_payload(user_token)
        user1_id = user1_data["sub"]

        category = db.query(HousingCategoryTableModel).first()
        assert category is not None

        create_payload = sample_offer_payload(user_id=user1_id, category_id=str(category.id))
        create_resp = client.post("/offers/", json=create_payload, headers={"Authorization": f"Bearer {user_token}"})
        assert create_resp.status_code == 201
        offer_id = create_resp.json()["id"]

        # user2 attempts to update it
        headers = {"Authorization": f"Bearer {user2_token}"}
        update_payload = {"title": "Attempted unauthorized update"}
        patch_resp = client.patch(f"/offers/{offer_id}", json=update_payload, headers=headers)
        print("Patch response JSON (unauthorized):", patch_resp.json())

        assert patch_resp.status_code == 403
        assert "Not authorized to update" in patch_resp.json()["detail"]

    def test_update_offer_not_found(self, client, admin_auth_headers):
        """Should return 404 when trying to update a non-existent offer."""
        random_id = uuid.uuid4()
        update_payload = {"title": "Does not exist"}

        resp = client.patch(f"/offers/{random_id}", json=update_payload, headers=admin_auth_headers)
        print("Patch response JSON (nonexistent offer):", resp.json())

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Offer not found."

    def test_update_offer_invalid_payload(self, client, admin_auth_headers, db):
        """Should return 422 when payload contains invalid data."""
        # Pick an existing offer
        offer = db.query(HousingOfferTableModel).first()
        assert offer is not None

        update_payload = {"price": "not-a-number"}  # invalid type
        resp = client.patch(f"/offers/{offer.id}", json=update_payload, headers=admin_auth_headers)
        print("Patch response JSON (invalid payload):", resp.json())

        assert resp.status_code == 422

    def test_delete_offer_as_owner(self, client, user_token, db):
        """Owner should be able to delete their own offer."""
        user_data = get_payload(user_token)
        user_id = user_data["sub"]

        category = db.query(HousingCategoryTableModel).first()
        assert category is not None

        # Create an offer as this user
        create_payload = sample_offer_payload(user_id=user_id, category_id=str(category.id))
        create_resp = client.post("/offers/", json=create_payload, headers={"Authorization": f"Bearer {user_token}"})
        assert create_resp.status_code == 201
        offer_id = create_resp.json()["id"]

        # Delete the offer
        delete_resp = client.delete(f"/offers/{offer_id}", headers={"Authorization": f"Bearer {user_token}"})
        print("Delete response status:", delete_resp.status_code)

        assert delete_resp.status_code == 204

        # Confirm it's removed from the DB
        deleted_offer = db.get(HousingOfferTableModel, uuid.UUID(offer_id))
        assert deleted_offer is None

    def test_delete_offer_as_admin(self, client, admin_auth_headers, user_token, db):
        """Admin should be able to delete any user's offer."""
        user_data = get_payload(user_token)
        user_id = user_data["sub"]

        category = db.query(HousingCategoryTableModel).first()
        assert category is not None

        # Create offer as a regular user
        create_payload = sample_offer_payload(user_id=user_id, category_id=str(category.id))
        create_resp = client.post("/offers/", json=create_payload, headers={"Authorization": f"Bearer {user_token}"})
        assert create_resp.status_code == 201
        offer_id = create_resp.json()["id"]

        # Delete as admin
        delete_resp = client.delete(f"/offers/{offer_id}", headers=admin_auth_headers)
        print("Delete response status (admin):", delete_resp.status_code)

        assert delete_resp.status_code == 204

        deleted_offer = db.get(HousingOfferTableModel, uuid.UUID(offer_id))
        assert deleted_offer is None

    def test_delete_offer_unauthorized_user(self, client, user_token, user2_token, db):
        """Non-owner, non-admin should get 403 when deleting an offer."""
        user_data = get_payload(user_token)
        user_id = user_data["sub"]

        category = db.query(HousingCategoryTableModel).first()
        assert category is not None

        # Create offer as user1
        create_payload = sample_offer_payload(user_id=user_id, category_id=str(category.id))
        create_resp = client.post("/offers/", json=create_payload, headers={"Authorization": f"Bearer {user_token}"})
        assert create_resp.status_code == 201
        offer_id = create_resp.json()["id"]

        # user2 tries to delete it
        headers = {"Authorization": f"Bearer {user2_token}"}
        delete_resp = client.delete(f"/offers/{offer_id}", headers=headers)
        print("Delete response JSON (unauthorized):", delete_resp.json())

        assert delete_resp.status_code == 403
        assert delete_resp.json()["detail"] == "Not authorized to delete this offer."

    def test_delete_offer_not_found(self, client, admin_auth_headers):
        """Deleting a nonexistent offer should return 404."""
        random_id = uuid.uuid4()
        delete_resp = client.delete(f"/offers/{random_id}", headers=admin_auth_headers)
        print("Delete response JSON (nonexistent):", delete_resp.json())

        assert delete_resp.status_code == 404
        assert delete_resp.json()["detail"] == "Offer not found."

