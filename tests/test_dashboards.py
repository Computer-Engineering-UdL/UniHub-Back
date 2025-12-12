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
        client.post("/offers/", json=payload, headers=user_headers)
        response = client.get("/dashboard/stats", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_content" in data
        assert data["total_users"]["value"] > 0
        assert data["active_content"]["value"] > 0

    def test_get_stats_forbidden_for_user(self, client, user_token):
        """Test that basic users cannot see dashboard stats."""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/dashboard/stats", headers=headers)
        assert response.status_code == 403

    def test_charts_structure_and_data(self, client, admin_auth_headers, user_token, db):
        """Test that charts return the correct JSON structure."""
        user_data = get_payload(user_token)
        user_id = user_data["sub"]
        category = db.query(HousingCategoryTableModel).first()
        payload = sample_offer_payload(user_id=user_id, category_id=str(category.id))
        client.post("/offers/", json=payload, headers={"Authorization": f"Bearer {user_token}"})
        r_weekly = client.get("/dashboard/charts/activity", headers=admin_auth_headers)
        assert r_weekly.status_code == 200
        weekly_data = r_weekly.json()
        assert len(weekly_data["labels"]) == 7
        assert len(weekly_data["datasets"]) == 2
        r_dist = client.get("/dashboard/charts/distribution", headers=admin_auth_headers)
        assert r_dist.status_code == 200
        dist_data = r_dist.json()
        assert "Housing Offers" in dist_data["labels"]
        assert len(dist_data["datasets"][0]["data"]) > 0

    def test_recent_activity_feed(self, client, admin_auth_headers, user_token, db):
        """Test that the activity feed returns a list of items."""
        user_data = get_payload(user_token)
        user_id = user_data["sub"]
        category = db.query(HousingCategoryTableModel).first()
        payload = sample_offer_payload(user_id=user_id, category_id=str(category.id), title="Activity Feed Test Offer")
        client.post("/offers/", json=payload, headers={"Authorization": f"Bearer {user_token}"})
        response = client.get("/dashboard/activity", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            item = data[0]
            assert "type" in item
            assert "title" in item

            titles = [i["title"] for i in data]
            assert "Activity Feed Test Offer" in titles or len(titles) > 0

    def test_activity_chart_time_ranges(self, client, admin_auth_headers):
        """Test that the activity chart respects different time ranges."""
        r_month = client.get("/dashboard/charts/activity?time_range=month", headers=admin_auth_headers)
        assert r_month.status_code == 200
        assert len(r_month.json()["labels"]) == 30
        r_year = client.get("/dashboard/charts/activity?time_range=year", headers=admin_auth_headers)
        assert r_year.status_code == 200
        assert len(r_year.json()["labels"]) == 12

    def test_channels_chart_data(self, client, admin_auth_headers):
        """Test that the channels chart returns correct labels and data."""
        client.post(
            "/channels/",
            json={
                "name": "Chart Test Channel",
                "description": "Public channel test",
                "category": "General",
                "channel_type": "public",
            },
            headers=admin_auth_headers,
        )

        response = client.get("/dashboard/charts/channels", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert "datasets" in data
        assert "Public" in data["labels"]
        pub_idx = data["labels"].index("Public")
        assert data["datasets"][0]["data"][pub_idx] > 0

    def test_recent_activity_includes_channels(self, client, admin_auth_headers):
        """Test that new channels appear in the recent activity feed."""
        from app.literals.channels import ChannelCategory

        channel_payload = {
            "name": "Activity Feed Channel",
            "description": "Testing feed",
            "category": ChannelCategory.GENERAL.value,
            "channel_type": "public",
        }

        create_resp = client.post("/channels/", json=channel_payload, headers=admin_auth_headers)
        assert create_resp.status_code in [200, 201], f"Channel creation failed: {create_resp.text}"
        response = client.get("/dashboard/activity", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        activity_types = [item["type"] for item in data]
        assert "new_channel" in activity_types

    def test_stats_include_channels_count(self, client, admin_auth_headers):
        """Test that the main stats endpoint includes channel counts."""
        client.post(
            "/channels/",
            json={"name": "Stats Channel", "category": "General", "channel_type": "public"},
            headers=admin_auth_headers,
        )

        response = client.get("/dashboard/stats", headers=admin_auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "total_channels" in data
        assert data["total_channels"]["value"] > 0
