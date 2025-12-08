import uuid

from app.core.config import settings
from app.literals.users import Role
from app.models import ConnectionTableModel, User, UserTermsAcceptanceTableModel


class TestAuthEndpoints:
    """Test authentication endpoints."""

    # --- Istniejące testy (działają, bo używają /auth/...) ---

    def test_login_success_username(self, client):
        """Test successful login with username."""
        response = client.post(
            "/auth/login",
            data={"username": "admin", "password": settings.DEFAULT_PASSWORD},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_success_email(self, client):
        response = client.post(
            "/auth/login",
            data={"username": "admin@admin.com", "password": settings.DEFAULT_PASSWORD},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_email(self, client):
        response = client.post(
            "/auth/login",
            data={"username": "nonexistent", "password": settings.DEFAULT_PASSWORD},
        )
        assert response.status_code == 401

    def test_login_wrong_password(self, client):
        response = client.post(
            "/auth/login",
            data={"username": "basic_user", "password": "invalidpassword"},
        )
        assert response.status_code == 401

    def test_login_invalid_payload(self, client):
        response = client.post("/auth/login", json={"email": "aniol0012@gmail.com"})
        assert response.status_code == 422

    def test_get_me_success(self, client):
        login_response = client.post(
            "/auth/login",
            data={"username": "admin", "password": settings.DEFAULT_PASSWORD},
        )
        token = login_response.json()["access_token"]
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["role"] == Role.ADMIN

    def test_get_me_without_token(self, client):
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_refresh_token(self, client):
        response = client.post(
            "/auth/login",
            data={"username": "admin", "password": settings.DEFAULT_PASSWORD},
        )
        assert response.status_code == 200
        data = response.json()
        refresh_resp = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
        assert refresh_resp.status_code == 200
        assert refresh_resp.json()["access_token"] != data["access_token"]

    def test_logout(self, client):
        response = client.post(
            "/auth/login",
            data={"username": "admin", "password": settings.DEFAULT_PASSWORD},
        )
        token = response.json()["access_token"]
        response = client.get("/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 205

    def test_logout_all(self, client):
        # Login 1
        r1 = client.post("/auth/login", data={"username": "admin", "password": settings.DEFAULT_PASSWORD})
        t1 = r1.json()["access_token"]
        # Login 2
        r2 = client.post("/auth/login", data={"username": "admin", "password": settings.DEFAULT_PASSWORD})
        t2 = r2.json()["access_token"]

        # Logout all using t1
        client.get("/auth/logout_all", headers={"Authorization": f"Bearer {t1}"})

        # Verify both are invalid
        assert client.get("/auth/me", headers={"Authorization": f"Bearer {t1}"}).status_code == 401
        assert client.get("/auth/me", headers={"Authorization": f"Bearer {t2}"}).status_code == 401


    def _create_terms(self, client, admin_headers, version):
        """Helper to ensure terms exist."""
        payload = {"version": version, "content": "Terms content for testing signup."}
        # Tutaj używamy API_VERSION, bo w conftest.py terms są podpięte z prefixem wersji
        resp = client.post(f"{settings.API_VERSION}/terms/", json=payload, headers=admin_headers)
        if resp.status_code == 201:
            return resp.json()["id"]
        return None


    def test_signup_success(self, client, db, admin_auth_headers):
        # 1. Prepare Terms
        terms_version = "vSignup-1.0"
        self._create_terms(client, admin_auth_headers, terms_version)

        # 2. Prepare Payload
        unique_suffix = str(uuid.uuid4())[:8]
        payload = {
            "email": f"newuser_{unique_suffix}@example.com",
            "username": f"user_{unique_suffix}",
            "password": "StrongPassword123!",
            "first_name": "New",
            "last_name": "User",
            "accepted_terms_version": terms_version,
            "referral_code": None
        }

        headers = {
            "X-Forwarded-For": "10.0.0.99",
            "User-Agent": "TestClient/1.0"
        }

        url = "/auth/signup"
        response = client.post(url, json=payload, headers=headers)

        assert response.status_code == 201, response.text
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Assert Database Side Effects
        user = db.query(User).filter_by(email=payload["email"]).first()
        assert user is not None
        assert user.created_ip == "10.0.0.99"

        conn = db.query(ConnectionTableModel).filter_by(user_id=user.id).first()
        assert conn is not None
        assert conn.ip_address == "10.0.0.99"

        terms_acc = db.query(UserTermsAcceptanceTableModel).filter_by(user_id=user.id).first()
        assert terms_acc is not None
        assert terms_acc.version == terms_version

    def test_signup_duplicate_email(self, client, user_token, admin_auth_headers):
        terms_version = "vSignup-Dup"
        self._create_terms(client, admin_auth_headers, terms_version)

        payload = {
            "email": "user@user.com",  # Existing email
            "username": "unique_username_123",
            "password": "password",
            "first_name": "Test",
            "last_name": "Test",
            "accepted_terms_version": terms_version
        }

        response = client.post("/auth/signup", json=payload)
        assert response.status_code == 409
        assert "Email already registered" in response.json()["detail"]

    def test_signup_duplicate_username(self, client, admin_auth_headers):
        terms_version = "vSignup-DupUser"
        self._create_terms(client, admin_auth_headers, terms_version)

        payload = {
            "email": "unique@email.com",
            "username": "basic_user",  # Existing username
            "password": "password",
            "first_name": "Test",
            "last_name": "Test",
            "accepted_terms_version": terms_version
        }

        response = client.post("/auth/signup", json=payload)
        assert response.status_code == 409
        assert "Username already taken" in response.json()["detail"]

    def test_signup_invalid_terms_version(self, client):
        payload = {
            "email": "valid@email.com",
            "username": "valid_user",
            "password": "password",
            "first_name": "Test",
            "last_name": "Test",
            "accepted_terms_version": "v.NON_EXISTENT_999"
        }

        response = client.post("/auth/signup", json=payload)
        assert response.status_code == 400
        assert "Invalid terms version" in response.json()["detail"]

    def test_signup_invalid_referral_code(self, client, admin_auth_headers):
        terms_version = "vSignup-Ref"
        self._create_terms(client, admin_auth_headers, terms_version)

        payload = {
            "email": "ref@email.com",
            "username": "ref_user",
            "password": "password",
            "first_name": "Test",
            "last_name": "Test",
            "accepted_terms_version": terms_version,
            "referral_code": "INVLD"
        }

        response = client.post("/auth/signup", json=payload)
        assert response.status_code == 400
        assert "Invalid referral code" in response.json()["detail"]

    def test_signup_validation_error(self, client):
        payload = {"email": "just@email.com"}
        response = client.post("/auth/signup", json=payload)
        assert response.status_code == 422