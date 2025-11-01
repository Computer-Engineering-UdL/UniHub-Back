import pytest

from app.literals.channels import ChannelCategory, ChannelRole
from app.literals.users import Role

# --- Helper Function ---


def _get_user_id(client, token):
    """Helper to get user ID from token."""
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    return response.json()["id"]


# --- Helper Fixtures ---


@pytest.fixture(scope="function")
def basic_user_id(client, user_token):
    return _get_user_id(client, user_token)


@pytest.fixture(scope="function")
def user2_id(client, user2_token):
    """Este es el ID de 'jane_smith', que tiene el rol SELLER."""
    return _get_user_id(client, user2_token)


@pytest.fixture(scope="function")
def admin_user_id(client, admin_token):
    return _get_user_id(client, admin_token)


class TestChannelCreationAndDeletion:
    """Tests for Req 1 (Admin Create) and Req 5 (Admin Delete)"""

    def test_admin_can_create_channel(self, client, admin_token):
        """(Req 1) Test Site Admin can create a channel."""
        response = client.post(
            "/channels/",
            json={
                "name": "Admin Test Channel",
                "description": "A test channel by admin",
                "channel_type": "public",
                "category": ChannelCategory.ENGINEERING,
                "required_role_read": Role.BASIC,
                "required_role_write": Role.SELLER,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Admin Test Channel"
        assert data["category"] == ChannelCategory.ENGINEERING
        assert data["required_role_read"] == Role.BASIC
        assert data["required_role_write"] == Role.SELLER
        assert "id" in data

    def test_user_cannot_create_channel(self, client, user_token):
        """Basic User cannot create a channel."""
        response = client.post(
            "/channels/",
            json={"name": "User Test Channel", "description": "A test channel by user"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_seller_cannot_create_channel(self, client, user2_token):
        """(Seller User cannot create a channel."""
        response = client.post(
            "/channels/",
            json={"name": "Seller Test Channel", "description": "A test channel by seller"},
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert response.status_code == 403

    def test_site_admin_can_delete_channel(self, client, admin_token):
        """Test Site Admin can delete a channel."""
        create_response = client.post(
            "/channels/",
            json={"name": "To Be Deleted"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_response.status_code == 200
        channel_id = create_response.json()["id"]

        response = client.delete(f"/channels/{channel_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        assert response.json() is True

    def test_channel_admin_cannot_delete_channel(self, client, admin_token, user2_token, user2_id):
        """Test a Channel Admin CANNOT delete a channel."""
        create_response = client.post(
            "/channels/",
            json={"name": "Channel Admin Delete Test"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_response.status_code == 200
        channel_id = create_response.json()["id"]
        add_response = client.post(
            f"/channels/{channel_id}/add_member/{user2_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert add_response.status_code == 200
        set_role_response = client.post(
            f"/channels/{channel_id}/set_role",
            json={"user_id": str(user2_id), "new_role": ChannelRole.ADMIN},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert set_role_response.status_code == 200
        response = client.delete(f"/channels/{channel_id}", headers={"Authorization": f"Bearer {user2_token}"})
        assert response.status_code == 403


@pytest.fixture(scope="function")
def setup_visibility_channels(client, admin_token):
    """Fixture to create channels with different read permissions."""
    response_basic = client.post(
        "/channels/",
        json={
            "name": "Basic Channel",
            "required_role_read": Role.BASIC,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    response_seller = client.post(
        "/channels/",
        json={
            "name": "Seller Channel",
            "required_role_read": Role.SELLER,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    response_admin = client.post(
        "/channels/",
        json={
            "name": "Admin-Only Channel",
            "required_role_read": Role.ADMIN,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response_basic.status_code == 200
    assert response_seller.status_code == 200
    assert response_admin.status_code == 200

    channels = {
        "basic_id": response_basic.json()["id"],
        "seller_id": response_seller.json()["id"],
        "admin_id": response_admin.json()["id"],
    }
    return channels


@pytest.mark.usefixtures("setup_visibility_channels")
class TestChannelVisibility:
    """Tests Role channel visibility."""

    def test_anonymous_sees_basic_channels_list(self, client, setup_visibility_channels):
        """anonymous user can list BASIC channels."""
        response = client.get("/channels/")
        assert response.status_code == 200
        data = response.json()
        channel_names = [c["name"] for c in data]

        assert "Basic Channel" in channel_names
        assert "Seller Channel" not in channel_names
        assert "Admin-Only Channel" not in channel_names

    def test_basic_user_sees_basic_channels_list(self, client, user_token, setup_visibility_channels):
        """basic user can list BASIC channels."""
        response = client.get("/channels/", headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 200
        data = response.json()
        channel_names = [c["name"] for c in data]

        assert "Basic Channel" in channel_names
        assert "Seller Channel" not in channel_names
        assert "Admin-Only Channel" not in channel_names

    def test_seller_sees_seller_and_basic_list(self, client, user2_token, setup_visibility_channels):
        """seller user can list SELLER and BASIC channels."""
        response = client.get("/channels/", headers={"Authorization": f"Bearer {user2_token}"})
        assert response.status_code == 200
        data = response.json()
        channel_names = [c["name"] for c in data]

        assert "Basic Channel" in channel_names
        assert "Seller Channel" in channel_names
        assert "Admin-Only Channel" not in channel_names

    def test_admin_sees_all_channels_list(self, client, admin_token, setup_visibility_channels):
        """admin user can list ALL channels."""
        response = client.get("/channels/", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        data = response.json()
        found_names = {c["name"] for c in data}
        assert "Basic Channel" in found_names
        assert "Seller Channel" in found_names
        assert "Admin-Only Channel" in found_names

    def test_anonymous_can_fetch_basic_channel(self, client, setup_visibility_channels):
        """anonymous user can GET a specific BASIC channel."""
        channel_id = setup_visibility_channels["basic_id"]
        response = client.get(f"/channels/{channel_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Basic Channel"

    def test_anonymous_cannot_fetch_seller_channel(self, client, setup_visibility_channels):
        """anonymous user CANNOT GET a specific SELLER channel."""
        channel_id = setup_visibility_channels["seller_id"]
        response = client.get(f"/channels/{channel_id}")
        assert response.status_code == 403  # Forbidden

    def test_user_cannot_fetch_seller_channel(self, client, user_token, setup_visibility_channels):
        """basic user CANNOT GET a specific SELLER channel."""
        channel_id = setup_visibility_channels["seller_id"]
        response = client.get(f"/channels/{channel_id}", headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 403  # Forbidden


@pytest.fixture(scope="function")
def setup_write_channels(client, admin_token, admin_user_id):
    """Fixture to create channels with different write permissions."""
    c1 = client.post(
        "/channels/",
        json={
            "name": "Write Basic",
            "required_role_read": Role.BASIC,
            "required_role_write": Role.BASIC,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()
    c2 = client.post(
        "/channels/",
        json={
            "name": "Write Seller",
            "required_role_read": Role.BASIC,
            "required_role_write": Role.SELLER,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()
    c3 = client.post(
        "/channels/",
        json={
            "name": "Write Admin",
            "required_role_read": Role.BASIC,
            "required_role_write": Role.ADMIN,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()
    c4 = client.post(
        "/channels/",
        json={
            "name": "Read Seller / Write Basic",
            "required_role_read": Role.SELLER,
            "required_role_write": Role.BASIC,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()
    channels = {
        "write_basic_id": c1["id"],
        "write_seller_id": c2["id"],
        "write_admin_id": c3["id"],
        "read_seller_id": c4["id"],
    }
    return channels


@pytest.mark.usefixtures("setup_write_channels")
class TestMessagePermissions:
    """Tests for Role message writing."""

    def test_user_can_write_in_basic_channel(self, client, user_token, basic_user_id, setup_write_channels):
        """Basic user can post in a Write=BASIC channel."""
        channel_id = setup_write_channels["write_basic_id"]
        response = client.post(
            f"/channels/{channel_id}/messages",
            json={"content": "Hello from basic user", "channel_id": channel_id, "user_id": str(basic_user_id)},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["content"] == "Hello from basic user"

    def test_user_cannot_write_in_seller_channel(self, client, user_token, basic_user_id, setup_write_channels):
        """Basic user CANNOT post in a Write=SELLER channel."""
        channel_id = setup_write_channels["write_seller_id"]
        response = client.post(
            f"/channels/{channel_id}/messages",
            json={"content": "Test", "channel_id": channel_id, "user_id": str(basic_user_id)},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403
        assert "You do not have permission to write" in response.json()["detail"]

    def test_seller_can_write_in_seller_channel(self, client, user2_token, user2_id, setup_write_channels):
        """Seller user can post in a Write=SELLER channel."""
        channel_id = setup_write_channels["write_seller_id"]
        response = client.post(
            f"/channels/{channel_id}/messages",
            json={"content": "Hello from seller", "channel_id": channel_id, "user_id": str(user2_id)},
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert response.status_code == 200
        assert response.json()["content"] == "Hello from seller"

    def test_seller_cannot_write_in_admin_channel(self, client, user2_token, user2_id, setup_write_channels):
        """Seller user CANNOT post in a Write=ADMIN channel."""
        channel_id = setup_write_channels["write_admin_id"]
        response = client.post(
            f"/channels/{channel_id}/messages",
            json={"content": "Test", "channel_id": channel_id, "user_id": str(user2_id)},
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert response.status_code == 403

    def test_user_cannot_write_if_cannot_read(self, client, user_token, basic_user_id, setup_write_channels):
        """Basic user CANNOT post in ANY channel they cannot read, even if Write=BASIC."""
        channel_id = setup_write_channels["read_seller_id"]
        response = client.post(
            f"/channels/{channel_id}/messages",
            json={"content": "Test", "channel_id": channel_id, "user_id": str(basic_user_id)},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403
        assert "You do not have permission to access" in response.json()["detail"]

    def test_anonymous_can_read_messages(self, client, setup_write_channels):
        """anonymous user can read messages from a BASIC channel."""
        channel_id = setup_write_channels["write_basic_id"]
        response = client.get(f"/channels/{channel_id}/messages")
        assert response.status_code == 200

    def test_anonymous_cannot_read_restricted_messages(self, client, setup_write_channels):
        """anonymous user CANNOT read messages from a SELLER channel."""
        channel_id = setup_write_channels["read_seller_id"]
        response = client.get(f"/channels/{channel_id}/messages")
        assert response.status_code == 403


@pytest.fixture(scope="function")
def setup_mod_channel(client, admin_token, admin_user_id, user2_id, basic_user_id):
    """Fixture to create a channel, a message, and promote a moderator."""
    c = client.post(
        "/channels/",
        json={"name": "Mod Test Channel", "required_role_read": Role.BASIC},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()
    channel_id = c["id"]
    add_resp = client.post(
        f"/channels/{channel_id}/add_member/{user2_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert add_resp.status_code == 200
    set_role_resp = client.post(
        f"/channels/{channel_id}/set_role",
        json={"user_id": str(user2_id), "new_role": ChannelRole.MODERATOR},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert set_role_resp.status_code == 200
    msg = client.post(
        f"/channels/{channel_id}/messages",
        json={"content": "Message to be deleted", "channel_id": channel_id, "user_id": str(admin_user_id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    return {"channel_id": channel_id, "message_id": msg["id"]}


@pytest.mark.usefixtures("setup_mod_channel")
class TestModerationAndRoles:
    """Tests for Role assignment and Mod deletes."""

    def test_site_admin_can_set_channel_role(self, client, admin_token, basic_user_id, setup_mod_channel):
        """Site Admin can assign a channel role (e.g., User -> Mod)."""
        channel_id = setup_mod_channel["channel_id"]
        add_resp = client.post(
            f"/channels/{channel_id}/add_member/{basic_user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert add_resp.status_code == 200
        response = client.post(
            f"/channels/{channel_id}/set_role",
            json={"user_id": str(basic_user_id), "new_role": ChannelRole.MODERATOR},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["role"] == ChannelRole.MODERATOR
        assert response.json()["user_id"] == str(basic_user_id)

    def test_non_admin_cannot_set_channel_role(
        self, client, admin_token, user2_token, basic_user_id, setup_mod_channel
    ):
        """Test non Site Admin cannot assign roles."""
        channel_id = setup_mod_channel["channel_id"]
        client.post(
            f"/channels/{channel_id}/add_member/{basic_user_id}", headers={"Authorization": f"Bearer {admin_token}"}
        )
        response = client.post(
            f"/channels/{channel_id}/set_role",
            json={"user_id": str(basic_user_id), "new_role": ChannelRole.ADMIN},
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert response.status_code == 403

    def test_moderator_can_delete_message(self, client, user2_token, setup_mod_channel):
        """Channel Moderator can delete a message."""
        channel_id = setup_mod_channel["channel_id"]
        message_id = setup_mod_channel["message_id"]
        response = client.delete(
            f"/channels/{channel_id}/messages/{message_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert response.status_code == 204  # No Content

    def test_user_cannot_delete_message(self, client, user_token, admin_token, admin_user_id, setup_mod_channel):
        """Basic User CANNOT delete a message."""
        channel_id = setup_mod_channel["channel_id"]
        msg = client.post(
            f"/channels/{channel_id}/messages",
            json={"content": "Another message", "channel_id": channel_id, "user_id": str(admin_user_id)},
            headers={"Authorization": f"Bearer {admin_token}"},
        ).json()
        message_id = msg["id"]
        response = client.delete(
            f"/channels/{channel_id}/messages/{message_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403  # Forbidden


@pytest.fixture(scope="function")
def setup_join_channels(client, admin_token):
    """Fixture to create channels for joining."""
    c1 = client.post(
        "/channels/",
        json={"name": "Join Basic", "required_role_read": Role.BASIC},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()
    c2 = client.post(
        "/channels/",
        json={"name": "Join Seller", "required_role_read": Role.SELLER},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()
    return {"basic_id": c1["id"], "seller_id": c2["id"]}


@pytest.mark.usefixtures("setup_join_channels")
class TestJoinLeave:
    """Tests Join and Leave endpoints."""

    def test_user_can_join_and_leave_basic_channel(self, client, user_token, setup_join_channels):
        """Basic user can join and leave a Read=BASIC channel."""
        channel_id = setup_join_channels["basic_id"]
        response_join = client.post(
            f"/channels/{channel_id}/join",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response_join.status_code == 200
        assert response_join.json()["role"] == ChannelRole.USER
        response_leave = client.post(
            f"/channels/{channel_id}/leave",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response_leave.status_code == 204

    def test_user_cannot_join_seller_channel(self, client, user_token, setup_join_channels):
        """Basic user CANNOT join a Read=SELLER channel."""
        channel_id = setup_join_channels["seller_id"]
        response = client.post(
            f"/channels/{channel_id}/join",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_seller_can_join_seller_channel(self, client, user2_token, setup_join_channels):
        """Seller user can join a Read=SELLER channel."""
        channel_id = setup_join_channels["seller_id"]
        response = client.post(
            f"/channels/{channel_id}/join",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert response.status_code == 200

    def test_leave_when_not_member(self, client, user_token, setup_join_channels):
        """Test leaving a channel you're not a member"""
        channel_id = setup_join_channels["basic_id"]
        client.post(
            f"/channels/{channel_id}/leave",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        response = client.post(
            f"/channels/{channel_id}/leave",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 404
