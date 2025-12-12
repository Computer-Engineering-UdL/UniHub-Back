import uuid

from app.literals.item import ItemSort
from app.models.item_category import ItemCategoryTableModel
from tests.factories.item_factory import sample_item_payload


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestItemEndpoints:
    def test_create_item_success(self, client, user_token, db):
        """Happy Path: Create a new marketplace item successfully."""
        category = db.query(ItemCategoryTableModel).filter_by(name="Electronics").first()
        assert category is not None, "Categories not seeded! Check seed_item_categories in conftest."
        payload = sample_item_payload(category_id=str(category.id))
        response = client.post("/items/", json=payload, headers=_auth(user_token))
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["price"] == payload["price"]
        assert data["owner_details"] is not None
        assert data["category"]["name"] == "Electronics"

    def test_create_item_invalid_price(self, client, user_token, db):
        """Validation: Price must be non-negative."""
        category = db.query(ItemCategoryTableModel).first()
        payload = sample_item_payload(category_id=str(category.id), price=-50.0)
        response = client.post("/items/", json=payload, headers=_auth(user_token))
        assert response.status_code == 422

    def test_create_item_invalid_category(self, client, user_token):
        """Integrity: Error if the category UUID does not exist."""
        fake_uuid = str(uuid.uuid4())
        payload = sample_item_payload(category_id=fake_uuid)

        response = client.post("/items/", json=payload, headers=_auth(user_token))
        assert response.status_code == 400
        assert "Invalid Category ID" in response.text

    def test_list_items_pagination(self, client, user_token, db):
        """Pagination: Verify page and page_size parameters."""
        category = db.query(ItemCategoryTableModel).first()
        # Create 3 items
        for i in range(3):
            p = sample_item_payload(category_id=str(category.id), title=f"Item {i}")
            client.post("/items/", json=p, headers=_auth(user_token))
        response = client.get("/items/?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] >= 3
        assert data["pages"] >= 2

    def test_list_items_search_filter(self, client, user_token, db):
        """Filter: Search by text in title."""
        category = db.query(ItemCategoryTableModel).first()
        client.post(
            "/items/",
            json=sample_item_payload(category_id=str(category.id), title="Gaming Mouse"),
            headers=_auth(user_token),
        )
        client.post(
            "/items/",
            json=sample_item_payload(category_id=str(category.id), title="Office Chair"),
            headers=_auth(user_token),
        )
        response = client.get("/items/?search=Mouse")
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["title"] == "Gaming Mouse"

    def test_list_items_price_range_filter(self, client, user_token, db):
        """Filter: Filter by min and max price range."""
        category = db.query(ItemCategoryTableModel).first()
        client.post(
            "/items/", json=sample_item_payload(category_id=str(category.id), price=10), headers=_auth(user_token)
        )
        client.post(
            "/items/", json=sample_item_payload(category_id=str(category.id), price=50), headers=_auth(user_token)
        )
        client.post(
            "/items/", json=sample_item_payload(category_id=str(category.id), price=100), headers=_auth(user_token)
        )
        response = client.get("/items/?min_price=20&max_price=80")
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["price"] == 50

    def test_list_items_location_filter(self, client, user_token, db):
        """Filter: Filter by location (case insensitive)."""
        category = db.query(ItemCategoryTableModel).first()
        client.post(
            "/items/",
            json=sample_item_payload(category_id=str(category.id), location="Madrid"),
            headers=_auth(user_token),
        )
        client.post(
            "/items/",
            json=sample_item_payload(category_id=str(category.id), location="Barcelona"),
            headers=_auth(user_token),
        )
        response = client.get("/items/?location=madrid")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        assert response.json()["items"][0]["location"] == "Madrid"

    def test_list_items_sort_price_asc(self, client, user_token, db):
        """Sorting: Order by price ascending."""
        category = db.query(ItemCategoryTableModel).first()
        client.post(
            "/items/", json=sample_item_payload(category_id=str(category.id), price=100), headers=_auth(user_token)
        )
        client.post(
            "/items/", json=sample_item_payload(category_id=str(category.id), price=10), headers=_auth(user_token)
        )
        response = client.get(f"/items/?sort={ItemSort.PRICE_ASC.value}")
        items = response.json()["items"]
        assert items[0]["price"] <= items[1]["price"]

    def test_get_item_detail_success(self, client, user_token, db):
        """Detail: Retrieve details of an existing item."""
        category = db.query(ItemCategoryTableModel).first()
        create_resp = client.post(
            "/items/", json=sample_item_payload(category_id=str(category.id)), headers=_auth(user_token)
        )
        item_id = create_resp.json()["id"]
        get_resp = client.get(f"/items/{item_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == item_id

    def test_get_item_not_found(self, client):
        """Error: Non-existent ID returns 404."""
        random_id = str(uuid.uuid4())
        response = client.get(f"/items/{random_id}")
        assert response.status_code == 404

    def test_update_item_success(self, client, user_token, db):
        """Update: The owner can successfully update the item."""
        category = db.query(ItemCategoryTableModel).first()
        create_resp = client.post(
            "/items/", json=sample_item_payload(category_id=str(category.id)), headers=_auth(user_token)
        )
        item_id = create_resp.json()["id"]
        update_payload = {"title": "Updated Title", "price": 999.99}
        response = client.patch(f"/items/{item_id}", json=update_payload, headers=_auth(user_token))
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"
        assert response.json()["price"] == 999.99

    def test_update_item_forbidden(self, client, user_token, user2_token, db):
        """Security: A different user cannot update the item (403 Forbidden)."""
        category = db.query(ItemCategoryTableModel).first()
        create_resp = client.post(
            "/items/", json=sample_item_payload(category_id=str(category.id)), headers=_auth(user_token)
        )
        item_id = create_resp.json()["id"]
        response = client.patch(f"/items/{item_id}", json={"title": "Hacked"}, headers=_auth(user2_token))
        assert response.status_code == 403

    def test_delete_item_soft_delete(self, client, user_token, db):
        """Delete: Verify soft delete logic and ensure it disappears from detail view."""
        category = db.query(ItemCategoryTableModel).first()
        create_resp = client.post(
            "/items/", json=sample_item_payload(category_id=str(category.id)), headers=_auth(user_token)
        )
        item_id = create_resp.json()["id"]
        del_resp = client.delete(f"/items/{item_id}", headers=_auth(user_token))
        assert del_resp.status_code == 204
        get_resp = client.get(f"/items/{item_id}")
        assert get_resp.status_code == 404

    def test_list_categories(self, client, db):
        """Categories: Verify that available categories are listed."""
        response = client.get("/item-categories/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        names = [c["name"] for c in data]
        assert "Electronics" in names
