import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.auth import DEFAULT_PASSWORD
from app.api.v1.endpoints.auth import router as auth_router


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestAuthEndpoints:
    def test_login_success(self, client):
        response = client.post("/auth/login", json={"email": "admin@admin.com", "password": DEFAULT_PASSWORD})
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@admin.com"

    def test_login_wrong_email(self, client):
        response = client.post("/auth/login", json={"email": "noexiste@correo.com", "password": DEFAULT_PASSWORD})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_wrong_password(self, client):
        response = client.post("/auth/login", json={"email": "admin@admin.com", "password": "incorrecta"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_invalid_payload(self, client):
        response = client.post("/auth/login", json={"email": "admin@admin.com"})
        assert response.status_code == 422
