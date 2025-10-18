import uuid
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints import channel as channel_router


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(channel_router.router, prefix="/channels")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# =========================
# Helpers
# =========================
def make_channel_dict(**overrides):
    data = {
        "id": str(uuid.uuid4()),
        "name": "general",
        "description": "Default channel",
        "channel_type": "public",
        "created_at": datetime.now(timezone.utc),
        "channel_logo": None,
    }
    data.update(overrides)
    return data


def make_membership_dict(**overrides):
    data = {
        "user_id": str(uuid.uuid4()),
        "channel_id": str(uuid.uuid4()),
        "role": "user",
        "joined_at": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return data


# =========================
# Tests
# =========================
class TestChannelEndpointsSimple:
    def test_fetch_channels(self, client, monkeypatch):
        channels = [
            make_channel_dict(name="general"),
            make_channel_dict(name="random"),
        ]
        monkeypatch.setattr(
            "app.crud.channel.ChannelCRUD.get_all",
            staticmethod(lambda db: channels),
        )

        r = client.get("/channels/")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "general"

    def test_fetch_channel_found(self, client, monkeypatch):
        ch = make_channel_dict(name="announcements")
        monkeypatch.setattr(
            "app.crud.channel.ChannelCRUD.get_by_id",
            staticmethod(lambda db, cid: ch),
        )

        r = client.get(f"/channels/{ch['id']}")
        assert r.status_code == 200
        assert r.json()["name"] == "announcements"

    def test_fetch_channel_not_found(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.crud.channel.ChannelCRUD.get_by_id",
            staticmethod(lambda db, cid: None),
        )

        r = client.get(f"/channels/{uuid.uuid4()}")
        assert r.status_code in (404, 400)

    def test_create_channel(self, client, monkeypatch):
        created = make_channel_dict(name="new-channel", description="A brand new one")
        monkeypatch.setattr(
            "app.crud.channel.ChannelCRUD.create",
            staticmethod(lambda db, payload: created),
        )

        payload = {"name": "new-channel", "description": "A brand new one", "channel_type": "public"}
        r = client.post("/channels/", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "new-channel"
        assert data["description"] == "A brand new one"

    def test_update_channel(self, client, monkeypatch):
        updated = make_channel_dict(name="general-updated", description="Updated desc")
        monkeypatch.setattr(
            "app.crud.channel.ChannelCRUD.update",
            staticmethod(lambda db, cid, payload: updated),
        )

        cid = updated["id"]
        r = client.patch(f"/channels/{cid}", json={"name": "general-updated", "description": "Updated desc"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "general-updated"
        assert data["description"] == "Updated desc"

    def test_delete_channel_success(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.crud.channel.ChannelCRUD.delete",
            staticmethod(lambda db, cid: True),
        )

        r = client.delete(f"/channels/{uuid.uuid4()}")
        assert r.status_code == 200
        assert r.json() is True

    def test_delete_channel_not_found(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.crud.channel.ChannelCRUD.delete",
            staticmethod(lambda db, cid: False),
        )

        r = client.delete(f"/channels/{uuid.uuid4()}")
        assert r.status_code == 200
        assert r.json() is False

    def test_add_member(self, client, monkeypatch):
        membership = make_membership_dict(role="moderator")
        chan_id = membership["channel_id"]
        user_id = membership["user_id"]

        monkeypatch.setattr(
            "app.crud.channel.ChannelCRUD.add_member",
            staticmethod(lambda db, cid, uid: membership),
        )

        r = client.post(f"/channels/{chan_id}/add_member/{user_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["channel_id"] == chan_id
        assert data["user_id"] == user_id
        assert data["role"] == "moderator"

    def test_remove_member_success(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.crud.channel.ChannelCRUD.remove_member",
            staticmethod(lambda db, cid, uid: True),
        )

        r = client.post(f"/channels/{uuid.uuid4()}/remove_member/{uuid.uuid4()}")
        assert r.status_code == 200
        assert r.json() is True

    def test_remove_member_not_found(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.crud.channel.ChannelCRUD.remove_member",
            staticmethod(lambda db, cid, uid: False),
        )

        r = client.post(f"/channels/{uuid.uuid4()}/remove_member/{uuid.uuid4()}")
        assert r.status_code == 200
        assert r.json() is False
