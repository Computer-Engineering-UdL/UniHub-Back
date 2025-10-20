from app.models import Interest, User
from app.seeds.interests import INTEREST_CATALOG


class TestInterestEndpoints:
    """Integration tests for interest endpoints."""

    def test_list_interest_categories_returns_seeded_catalog(self, client):
        response = client.get("/interest/")
        assert response.status_code == 200
        data = response.json()

        assert len(data) == len(INTEREST_CATALOG)
        response_names = {category["name"] for category in data}
        assert response_names == set(INTEREST_CATALOG.keys())

        for category in data:
            expected = set(INTEREST_CATALOG[category["name"]])
            received = {interest["name"] for interest in category["interests"]}
            assert received == expected

    def test_user_interest_crud_flow(self, client, db, auth_headers):
        user: User = db.query(User).filter_by(username="testuser").first()
        assert user is not None

        interest: Interest = db.query(Interest).first()
        assert interest is not None

        response = client.post(
            f"/interest/user/{user.id}",
            json={"interest_id": str(interest.id)},
            headers=auth_headers,
        )
        assert response.status_code == 201
        payload = response.json()
        assert any(item["id"] == str(interest.id) for item in payload)

        conflict_response = client.post(
            f"/interest/user/{user.id}",
            json={"interest_id": str(interest.id)},
            headers=auth_headers,
        )
        assert conflict_response.status_code == 409

        list_response = client.get(f"/interest/user/{user.id}")
        assert list_response.status_code == 200
        listed = list_response.json()
        assert [item["id"] for item in listed] == [str(interest.id)]

        delete_response = client.delete(
            f"/interest/user/{user.id}/{interest.id}",
            headers=auth_headers,
        )
        assert delete_response.status_code == 204

        after_delete = client.get(f"/interest/user/{user.id}")
        assert after_delete.status_code == 200
        assert after_delete.json() == []
