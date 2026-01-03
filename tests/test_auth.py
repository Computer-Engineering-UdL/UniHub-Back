import uuid

import pytest

from app.core.config import settings
from app.literals.users import Role
from app.models import ConnectionTableModel, User, UserTermsAcceptanceTableModel


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


class FakeOAuthClient:
    def __init__(self, token_data=None, get_responses=None):
        self.token_data = token_data or {}
        self.get_responses = get_responses or []
        self.get_call_count = 0

    async def authorize_access_token(self, request):
        return self.token_data

    async def authorize_redirect(self, request, redirect_uri):
        from starlette.responses import RedirectResponse

        return RedirectResponse(url="http://test.com")

    async def get(self, url, token=None):
        data = {}
        if self.get_call_count < len(self.get_responses):
            data = self.get_responses[self.get_call_count]
            self.get_call_count += 1
        return FakeResponse(data)


class FakeOAuth:
    def __init__(self, client):
        self.client = client

    def create_client(self, name):
        return self.client


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
        resp = client.post("/terms/", json=payload, headers=admin_headers)
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
            "referral_code": None,
        }

        headers = {"X-Forwarded-For": "10.0.0.99", "User-Agent": "TestClient/1.0"}

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
        }

        response = client.post("/auth/signup", json=payload)
        assert response.status_code == 409
        assert "Username already taken" in response.json()["detail"]

    def test_signup_invalid_referral_code(self, client, admin_auth_headers):
        terms_version = "vSignup-Ref"
        self._create_terms(client, admin_auth_headers, terms_version)

        payload = {
            "email": "ref@email.com",
            "username": "ref_user",
            "password": "password",
            "first_name": "Test",
            "last_name": "Test",
            "referral_code": "INVLD",
        }

        response = client.post("/auth/signup", json=payload)
        assert response.status_code == 400
        assert "Invalid referral code" in response.json()["detail"]

    def test_signup_validation_error(self, client):
        payload = {"email": "just@email.com"}
        response = client.post("/auth/signup", json=payload)
        assert response.status_code == 422

    def test_login_oauth_redirect(self, client, app):
        """Test that login_oauth redirects."""
        from app.api.dependencies import get_oauth

        fake_client = FakeOAuthClient()
        fake_oauth = FakeOAuth(fake_client)

        app.dependency_overrides[get_oauth] = lambda: fake_oauth

        response = client.get("/auth/google", follow_redirects=False)

        assert response.status_code in (302, 307), response.text
        assert response.headers["location"] == "http://test.com"

        app.dependency_overrides = {}

    def test_oauth_callback_google_signup_success(self, client, db, app, admin_auth_headers):
        """Test OAuth signup via Google."""
        from app.api.dependencies import get_oauth

        terms_version = "vGoogle-1.0"
        self._create_terms(client, admin_auth_headers, terms_version)

        user_email = "google_user@example.com"
        token_data = {
            "userinfo": {
                "email": user_email,
                "given_name": "Google",
                "family_name": "User",
                "picture": "http://img.com/pic",
            }
        }
        fake_client = FakeOAuthClient(token_data=token_data)
        fake_oauth = FakeOAuth(fake_client)
        app.dependency_overrides[get_oauth] = lambda: fake_oauth

        # Login to set cookie
        client.get("/auth/google", follow_redirects=False)

        response = client.get("/auth/google/callback")

        assert response.status_code == 200, response.text
        data = response.json()
        assert "access_token" in data

        user = db.query(User).filter_by(email=user_email).first()
        assert user is not None
        assert user.provider == "google"
        assert user.is_verified is True

        app.dependency_overrides = {}

    @pytest.mark.no_seed
    def test_oauth_callback_fails_no_active_terms(self, client, app):
        """Test that OAuth signup fails if no terms exist in system."""
        from app.api.dependencies import get_oauth

        token_data = {"userinfo": {"email": "no_terms@example.com"}}
        fake_client = FakeOAuthClient(token_data=token_data)
        fake_oauth = FakeOAuth(fake_client)
        app.dependency_overrides[get_oauth] = lambda: fake_oauth

        response = client.get("/auth/google/callback")

        assert response.status_code == 500
        assert "No active terms found" in response.json()["detail"]

        app.dependency_overrides = {}

    def test_oauth_callback_existing_user_login(self, client, db, app):
        """Test existing user login via OAuth doesn't require terms."""
        from app.api.dependencies import get_oauth
        from app.core.security import hash_password

        email = "existing_oauth@example.com"
        user = User(
            username="existing_oauth",
            email=email,
            password=hash_password("pw"),
            first_name="Ex",
            last_name="Isting",
            provider="google",
            is_active=True,
            referral_code="OAUTH",
        )
        db.add(user)
        db.commit()

        token_data = {"userinfo": {"email": email}}
        fake_client = FakeOAuthClient(token_data=token_data)
        fake_oauth = FakeOAuth(fake_client)
        app.dependency_overrides[get_oauth] = lambda: fake_oauth

        response = client.get("/auth/google/callback")

        assert response.status_code == 200
        assert "access_token" in response.json()

        app.dependency_overrides = {}

    def test_oauth_callback_github_signup(self, client, db, app, admin_auth_headers):
        """Test OAuth signup via GitHub."""
        from app.api.dependencies import get_oauth

        terms_version = "vGitHub-1.0"
        self._create_terms(client, admin_auth_headers, terms_version)

        email = "github_user@example.com"
        token_data = {"access_token": "gh_token"}
        # Responses for .get calls: [emails, user_profile]
        get_responses = [[{"email": email, "primary": True}], {"login": "github_dev", "avatar_url": "http://gh"}]

        fake_client = FakeOAuthClient(token_data=token_data, get_responses=get_responses)
        fake_oauth = FakeOAuth(fake_client)
        app.dependency_overrides[get_oauth] = lambda: fake_oauth

        # Login to set cookie
        client.get("/auth/github", follow_redirects=False)

        response = client.get("/auth/github/callback")

        assert response.status_code == 200, response.text

        user = db.query(User).filter_by(email=email).first()
        assert user is not None
        assert user.provider == "github"

        app.dependency_overrides = {}
