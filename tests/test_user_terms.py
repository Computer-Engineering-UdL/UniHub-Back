from app.core.config import settings


def create_term(client, admin_headers, version: str) -> str:
    """Helper to create a term and return its ID."""
    payload = {
        "version": version,
        "content": f"Content for {version}"
    }
    url = f"{settings.API_VERSION}/terms/"
    resp = client.post(url, json=payload, headers=admin_headers)
    assert resp.status_code == 201
    return resp.json()["id"]


class TestUserTermsEndpoints:

    def test_accept_latest_terms_success(self, client, auth_headers, admin_auth_headers):
        """User should be able to accept the latest terms."""
        # 1. Admin creates Terms v1
        term_id = create_term(client, admin_auth_headers, "v1.0-ACCEPT")

        # 2. User accepts
        url = f"{settings.API_VERSION}/user_terms/accept"
        resp = client.post(url, headers=auth_headers)

        assert resp.status_code == 201
        data = resp.json()
        assert data["terms_id"] == term_id
        assert "accepted_at" in data


    def test_accept_terms_idempotency(self, client, auth_headers, admin_auth_headers):
        """Calling accept twice should return the same record (not error)."""
        create_term(client, admin_auth_headers, "v1.0-IDEM")

        url = f"{settings.API_VERSION}/user_terms/accept"

        # First call
        resp1 = client.post(url, headers=auth_headers)
        assert resp1.status_code == 201
        id1 = resp1.json()["id"]

        # Second call
        resp2 = client.post(url, headers=auth_headers)
        assert resp2.status_code == 201
        id2 = resp2.json()["id"]

        assert id1 == id2  # Should be the same acceptance record


    def test_get_latest_status_flow(self, client, auth_headers, admin_auth_headers):
        """
        Full flow:
        1. Create v1 -> Status: False
        2. Accept v1 -> Status: True
        3. Create v2 -> Status: False (because v2 is newer)
        4. Accept v2 -> Status: True
        """
        status_url = f"{settings.API_VERSION}/user_terms/latest-status"
        accept_url = f"{settings.API_VERSION}/user_terms/accept"

        # 1. Create v1
        v1_id = create_term(client, admin_auth_headers, "v1-FLOW")

        # Check status (should be False)
        resp = client.get(status_url, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["accepted_latest"] is False
        assert data["latest_terms_id"] == v1_id

        # 2. Accept v1
        client.post(accept_url, headers=auth_headers)

        # Check status (should be True)
        resp = client.get(status_url, headers=auth_headers)
        assert resp.json()["accepted_latest"] is True
        assert resp.json()["user_last_accepted_terms_id"] == v1_id

        # 3. Create v2 (newer)
        v2_id = create_term(client, admin_auth_headers, "v2-FLOW")

        # Check status (should be False again, because v2 is now latest)
        resp = client.get(status_url, headers=auth_headers)
        data = resp.json()
        assert data["accepted_latest"] is False
        assert data["latest_terms_id"] == v2_id
        assert data["user_last_accepted_terms_id"] == v1_id  # Still points to v1

        # 4. Accept v2
        client.post(accept_url, headers=auth_headers)

        # Check status (should be True)
        resp = client.get(status_url, headers=auth_headers)
        data = resp.json()
        assert data["accepted_latest"] is True
        assert data["user_last_accepted_terms_id"] == v2_id


    def test_list_user_acceptances(self, client, auth_headers, admin_auth_headers):
        """Should list all versions accepted by user."""
        list_url = f"{settings.API_VERSION}/user_terms/user/list"
        accept_url = f"{settings.API_VERSION}/user_terms/accept"

        # Initial check (might be empty or contain seeded terms)
        initial_resp = client.get(list_url, headers=auth_headers)
        initial_count = len(initial_resp.json())

        # Create & Accept v1
        create_term(client, admin_auth_headers, "v1-LIST")
        client.post(accept_url, headers=auth_headers)

        # Create & Accept v2
        create_term(client, admin_auth_headers, "v2-LIST")
        client.post(accept_url, headers=auth_headers)

        # Check list
        resp = client.get(list_url, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        assert len(data) == initial_count + 2

        # Verify structure
        assert "terms_id" in data[0]
        assert "version" in data[0]
        assert "accepted_at" in data[0]

        versions = [item["version"] for item in data]
        assert "v1-LIST" in versions
        assert "v2-LIST" in versions