import uuid

from app.core.security import get_payload


class TestConnectionEndpoints:
    def test_log_connection_basic_user(self, client, user_token, auth_headers):
        """
        Basic user logs their own connection.
        """
        user_data = get_payload(user_token)
        user_id = user_data["sub"]

        payload = {"user_id": user_id, "ip_address": "192.168.1.100"}

        url = "/connection/"
        resp = client.post(url, json=payload, headers=auth_headers)

        assert resp.status_code == 201
        data = resp.json()
        assert data["ip_address"] == "192.168.1.100"
        assert data["user_id"] == user_id
        assert "connection_date" in data

    def test_log_connection_spoof_attempt(self, client, user_token, auth_headers):
        """
        Basic user tries to log connection for another user (spoofing).
        The backend should overwrite the user_id with the token's user_id.
        """
        user_data = get_payload(user_token)
        real_user_id = user_data["sub"]
        fake_user_id = str(uuid.uuid4())

        payload = {
            "user_id": fake_user_id,  # Trying to fake it
            "ip_address": "10.0.0.5",
        }

        url = "/connection/"
        resp = client.post(url, json=payload, headers=auth_headers)

        assert resp.status_code == 201
        data = resp.json()

        # Verify the backend corrected the user_id
        assert data["user_id"] == real_user_id
        assert data["user_id"] != fake_user_id

    def test_log_connection_as_admin_for_other(self, client, admin_auth_headers):
        """
        Admin logs connection for a random user ID (e.g., manual audit log).
        Admin is allowed to set any user_id.
        """
        target_user_id = str(uuid.uuid4())
        payload = {"user_id": target_user_id, "ip_address": "8.8.8.8"}

        url = "/connection/"
        resp = client.post(url, json=payload, headers=admin_auth_headers)

        assert resp.status_code == 201
        data = resp.json()
        assert data["user_id"] == target_user_id

    def test_log_connection_invalid_ip(self, client, auth_headers, user_token):
        """Should return 400 for invalid IP format."""
        user_data = get_payload(user_token)
        user_id = user_data["sub"]

        payload = {"user_id": user_id, "ip_address": "not-an-ip-address"}

        url = "/connection/"
        resp = client.post(url, json=payload, headers=auth_headers)

        # Service rzuca ValueError -> HTTPException 400
        assert resp.status_code == 400
        assert "Invalid IP address" in resp.json()["detail"]

    def test_get_my_connection_history(self, client, user_token, auth_headers):
        """User retrieves their own history."""
        user_data = get_payload(user_token)
        user_id = user_data["sub"]

        # Log a few connections first
        url_log = "/connection/"
        client.post(url_log, json={"user_id": user_id, "ip_address": "1.1.1.1"}, headers=auth_headers)
        client.post(url_log, json={"user_id": user_id, "ip_address": "2.2.2.2"}, headers=auth_headers)

        # Get history
        url_me = "/connection/me"
        resp = client.get(url_me, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2

        # Check if IPs are present
        ips = [c["ip_address"] for c in data]
        assert "1.1.1.1" in ips
        assert "2.2.2.2" in ips

    def test_get_history_by_user_id_as_admin(self, client, admin_auth_headers, user_token, auth_headers):
        """Admin views basic user's history."""
        user_data = get_payload(user_token)
        target_user_id = user_data["sub"]

        # Generate some data
        url_log = "/connection/"
        client.post(url_log, json={"user_id": target_user_id, "ip_address": "10.10.10.10"}, headers=auth_headers)

        url_get = f"/connection/user/{target_user_id}"
        resp = client.get(url_get, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        assert data[0]["user_id"] == target_user_id
        assert data[0]["ip_address"] == "10.10.10.10"

    def test_get_history_by_user_id_forbidden(self, client, auth_headers):
        """Basic user tries to view another user's history."""
        random_user_id = str(uuid.uuid4())

        url_get = f"/connection/user/{random_user_id}"
        resp = client.get(url_get, headers=auth_headers)

        assert resp.status_code == 403
        assert "Admin privileges required" in resp.json()["detail"]

    def test_get_own_history_by_id_allowed(self, client, user_token, auth_headers):
        """User tries to view THEIR OWN history via /user/{id}. Should be allowed."""
        user_data = get_payload(user_token)
        my_id = user_data["sub"]

        url_get = f"/connection/user/{my_id}"
        resp = client.get(url_get, headers=auth_headers)

        assert resp.status_code == 200

    def test_search_by_ip_as_admin(self, client, admin_auth_headers, auth_headers, user_token):
        """Admin searches connections by IP."""
        target_ip = "123.123.123.123"
        user_data = get_payload(user_token)
        user_id = user_data["sub"]

        # Log connection
        url_log = "/connection/"
        client.post(url_log, json={"user_id": user_id, "ip_address": target_ip}, headers=auth_headers)

        # Search
        url_search = f"/connection/ip/{target_ip}"
        resp = client.get(url_search, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["ip_address"] == target_ip
        assert data[0]["user_id"] == user_id

    def test_search_by_ip_forbidden(self, client, auth_headers):
        """Basic user tries to search by IP."""
        url_search = "/connection/ip/1.1.1.1"
        resp = client.get(url_search, headers=auth_headers)

        assert resp.status_code == 403
        assert "Admin privileges required" in resp.json()["detail"]
