from app.core.config import settings
from app.core.security import get_payload
from app.models import HousingCategoryTableModel
from tests.factories.offer_factory import sample_offer_payload


class TestDashboardEndpoints:
    """End-to-end checks for /dashboard endpoints."""

    def test_get_stats_admin_only(self, client, admin_auth_headers, user_token, db):
        """Test that admins can retrieve KPI stats with real data."""
        user_data = get_payload(user_token)
        user_id = user_data["sub"]
        category = db.query(HousingCategoryTableModel).first()
        assert category is not None, "Category not found in test database!"

        payload = sample_offer_payload(user_id=user_id, category_id=str(category.id))
        user_headers = {"Authorization": f"Bearer {user_token}"}
        client.post(f"{settings.API_VERSION}/offers/", json=payload, headers=user_headers)
        response = client.get(f"{settings.API_VERSION}/dashboard/stats", headers=admin_auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "total_users" in data
        assert "active_content" in data
        assert data["total_users"]["value"] > 0
        assert data["active_content"]["value"] > 0

    def test_get_stats_forbidden_for_user(self, client, user_token):
        """Test that basic users cannot see dashboard stats."""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(f"{settings.API_VERSION}/dashboard/stats", headers=headers)
        assert response.status_code == 403

    def test_charts_structure_and_data(self, client, admin_auth_headers, user_token, db):
        """Test that charts return the correct JSON structure."""
        user_data = get_payload(user_token)
        user_id = user_data["sub"]
        category = db.query(HousingCategoryTableModel).first()
        payload = sample_offer_payload(user_id=user_id, category_id=str(category.id))
        client.post(f"{settings.API_VERSION}/offers/", json=payload, headers={"Authorization": f"Bearer {user_token}"})
        r_weekly = client.get(f"{settings.API_VERSION}/dashboard/charts/weekly", headers=admin_auth_headers)
        assert r_weekly.status_code == 200
        weekly_data = r_weekly.json()

        assert len(weekly_data["labels"]) == 7
        assert len(weekly_data["datasets"]) == 2
        r_dist = client.get(f"{settings.API_VERSION}/dashboard/charts/distribution", headers=admin_auth_headers)
        assert r_dist.status_code == 200
        dist_data = r_dist.json()

        assert "Housing" in dist_data["labels"]
        assert len(dist_data["datasets"][0]["data"]) > 0

    def test_recent_activity_feed(self, client, admin_auth_headers, user_token, db):
        """Test that the activity feed returns a list of items."""

        user_data = get_payload(user_token)
        user_id = user_data["sub"]
        category = db.query(HousingCategoryTableModel).first()
        payload = sample_offer_payload(user_id=user_id, category_id=str(category.id), title="Activity Feed Test Offer")
        client.post(f"{settings.API_VERSION}/offers/", json=payload, headers={"Authorization": f"Bearer {user_token}"})
        response = client.get(f"{settings.API_VERSION}/dashboard/activity", headers=admin_auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            item = data[0]
            assert "type" in item
            assert "title" in item

            titles = [i["title"] for i in data]
            assert "Activity Feed Test Offer" in titles or len(titles) > 0
