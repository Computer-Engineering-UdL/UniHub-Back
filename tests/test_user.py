import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints import user as users_router


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(users_router.router, prefix="/users")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================
# Helpers
# =========================


def make_user_dict(**overrides):
    data = {
        "id": str(uuid.uuid4()),
        "username": "alice",
        "email": "alice@example.com",
        "first_name": "Alice",
        "last_name": "Doe",
        "provider": "local",
        "role": "Basic",
        "phone": None,
        "university": None,
    }
    data.update(overrides)
    return data


# =========================
# Tests
# =========================
class TestUsersEndpointsSimple:
    def test_create_user_success(self, client, monkeypatch):
        monkeypatch.setattr("app.api.v1.endpoints.user.hash_password", lambda p: "hashed:" + p)

        def fake_create(db, user_in):
            return make_user_dict(username=user_in.username, email=user_in.email, first_name=user_in.first_name)

        monkeypatch.setattr("app.crud.user.UserCRUD.create", staticmethod(fake_create))

        payload = {
            "username": "alice",
            "email": "alice@example.com",
            "first_name": "Alice",
            "last_name": "Doe",
            "password": "SuperSecret123",
            "provider": "local",
            "role": "Basic",
        }
        r = client.post("/users/", json=payload)
        assert r.status_code == 201
        data = r.json()
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"

    def test_get_user_found(self, client, monkeypatch):
        u = make_user_dict(username="bob", email="bob@example.com")
        monkeypatch.setattr("app.crud.user.UserCRUD.get_by_id", staticmethod(lambda db, uid: u))

        r = client.get(f"/users/{u['id']}")
        assert r.status_code == 200
        assert r.json()["username"] == "bob"

    def test_get_user_not_found(self, client, monkeypatch):
        monkeypatch.setattr("app.crud.user.UserCRUD.get_by_id", staticmethod(lambda db, uid: None))

        r = client.get(f"/users/{uuid.uuid4()}")
        assert r.status_code in (404, 400)

    def test_list_users(self, client, monkeypatch):
        users = [
            make_user_dict(username="u1", email="u1@example.com"),
            make_user_dict(username="u2", email="u2@example.com"),
        ]
        monkeypatch.setattr(
            "app.crud.user.UserCRUD.get_all", staticmethod(lambda db, skip=0, limit=100, search=None: users)
        )

        r = client.get("/users/?skip=0&limit=10")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["username"] == "u1"

    def test_update_user_success(self, client, monkeypatch):
        monkeypatch.setattr("app.api.v1.endpoints.user.hash_password", lambda p: "hashed:" + p)

        updated = make_user_dict(first_name="AliceUpdated")
        monkeypatch.setattr("app.crud.user.UserCRUD.update", staticmethod(lambda db, uid, user_in: updated))

        uid = updated["id"]
        r = client.patch(f"/users/{uid}", json={"first_name": "AliceUpdated", "password": "NewPassw0rd!"})
        assert r.status_code == 200
        assert r.json()["first_name"] == "AliceUpdated"

    def test_delete_user_success(self, client, monkeypatch):
        monkeypatch.setattr("app.crud.user.UserCRUD.delete", staticmethod(lambda db, uid: True))

        uid = str(uuid.uuid4())
        r = client.delete(f"/users/{uid}")
        assert r.status_code == 204

    def test_delete_user_not_found(self, client, monkeypatch):
        monkeypatch.setattr("app.crud.user.UserCRUD.delete", staticmethod(lambda db, uid: False))

        uid = str(uuid.uuid4())
        r = client.delete(f"/users/{uid}")
        assert r.status_code in (404, 400)
