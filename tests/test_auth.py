
from app.core.seed import DEFAULT_PASSWORD


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_success(self, client):
        """Test successful login."""
        response = client.post("/auth/login", data={"username": "admin", "password": DEFAULT_PASSWORD})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_email(self, client):
        """Test login with non-existent email."""
        response = client.post("/auth/login", data={"username": "nonexistent", "password": DEFAULT_PASSWORD})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        response = client.post("/auth/login", data={"username": "testuser", "password": "invalidpassword"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_invalid_payload(self, client):
        """Test login with missing password field."""
        response = client.post("/auth/login", json={"email": "aniol0012@gmail.com"})
        assert response.status_code == 422

    def test_get_me_success(self, client):
        """Test getting current user info."""
        login_response = client.post("/auth/login", data={"username": "admin", "password": DEFAULT_PASSWORD})
        token = login_response.json()["access_token"]

        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@admin.com"
        assert data["username"] == "admin"
        assert data["role"] == "Admin"

    def test_get_me_without_token(self, client):
        """Test getting current user without token."""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_refresh_token(self, client):
        """Test refresh token."""
        response = client.post("/auth/login", data={"username": "admin", "password": DEFAULT_PASSWORD})
        assert response.status_code == 200
        token: str = response.json()["access_token"]
        refresh_token: str = response.json()["refresh_token"]
        refresh_resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_resp.status_code == 200
        new_tokens = refresh_resp.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["access_token"] != token
