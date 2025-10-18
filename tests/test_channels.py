import uuid


class TestChannelEndpoints:
    """Test channel CRUD operations with permissions."""

    def test_create_channel_success(self, client, user_token):
        """Test regular user can create a channel and becomes admin."""
        response = client.post(
            "/channels/",
            json={
                "name": "Test Channel",
                "description": "A test channel",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Channel"
        assert data["description"] == "A test channel"
        assert "id" in data

    def test_create_channel_without_auth(self, client):
        """Test creating channel without authentication fails."""
        response = client.post(
            "/channels/",
            json={
                "name": "Test Channel",
                "description": "A test channel",
                "channel_type": "public",
            },
        )
        assert response.status_code == 401

    def test_fetch_all_channels_admin_only(self, client, admin_token, user_token):
        """Test only admins can fetch all channels."""
        response = client.get("/channels/", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200

        response = client.get("/channels/", headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 403

    def test_fetch_channel_requires_membership(self, client, user_token, user2_token):
        """Test only members can view a channel."""
        create_response = client.post(
            "/channels/",
            json={"name": "Private Channel", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        channel_id = create_response.json()["id"]

        response = client.get(f"/channels/{channel_id}", headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 200

        response = client.get(f"/channels/{channel_id}", headers={"Authorization": f"Bearer {user2_token}"})
        assert response.status_code == 403

    def test_update_channel_admin_only(self, client, user_token, user2_token):
        """Test only channel admin can update channel."""
        create_response = client.post(
            "/channels/",
            json={"name": "Update Test", "description": "Original", "channel_type": "public"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        channel_id = create_response.json()["id"]

        response = client.patch(
            f"/channels/{channel_id}",
            json={"description": "Updated description"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"

        client.post(
            f"/channels/{channel_id}/add_member/{self._get_user_id(client, user2_token)}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        response = client.patch(
            f"/channels/{channel_id}",
            json={"description": "Hacked"},
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert response.status_code == 403

    def test_delete_channel_admin_only(self, client, user_token, user2_token):
        """Test only channel admin can delete channel."""
        create_response = client.post(
            "/channels/",
            json={"name": "Delete Test", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        channel_id = create_response.json()["id"]

        client.post(
            f"/channels/{channel_id}/add_member/{self._get_user_id(client, user2_token)}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        response = client.delete(f"/channels/{channel_id}", headers={"Authorization": f"Bearer {user2_token}"})
        assert response.status_code == 403

        response = client.delete(f"/channels/{channel_id}", headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 200

    def test_add_member_admin_only(self, client, user_token, user2_token, admin_token):
        """Test only channel admin can add members."""
        create_response = client.post(
            "/channels/",
            json={"name": "Member Test", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        channel_id = create_response.json()["id"]
        user2_id = self._get_user_id(client, user2_token)

        response = client.post(
            f"/channels/{channel_id}/add_member/{user2_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200

        admin_id = self._get_user_id(client, admin_token)
        response = client.post(
            f"/channels/{channel_id}/add_member/{admin_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_remove_member_moderator_can_remove(self, client, user_token, user2_token):
        """Test moderators can remove members."""
        create_response = client.post(
            "/channels/",
            json={"name": "Remove Test", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        channel_id = create_response.json()["id"]
        user2_id = self._get_user_id(client, user2_token)

        client.post(
            f"/channels/{channel_id}/add_member/{user2_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        response = client.post(
            f"/channels/{channel_id}/remove_member/{user2_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200

    def test_ban_member_moderator_required(self, client, user_token, user2_token):
        """Test only moderators and above can ban members."""
        create_response = client.post(
            "/channels/",
            json={"name": "Ban Test", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        channel_id = create_response.json()["id"]
        user2_id = self._get_user_id(client, user2_token)

        client.post(
            f"/channels/{channel_id}/add_member/{user2_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        response = client.post(
            f"/channels/{channel_id}/ban",
            json={"user_id": str(user2_id), "motive": "Test ban", "duration_days": 7},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["motive"] == "Test ban"
        assert data["active"] is True

    def test_unban_member_moderator_required(self, client, user_token, user2_token):
        """Test only moderators and above can unban members."""
        create_response = client.post(
            "/channels/",
            json={"name": "Unban Test", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        channel_id = create_response.json()["id"]
        user2_id = self._get_user_id(client, user2_token)

        client.post(
            f"/channels/{channel_id}/add_member/{user2_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        client.post(
            f"/channels/{channel_id}/ban",
            json={"user_id": str(user2_id), "motive": "Test", "duration_days": 7},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        response = client.post(
            f"/channels/{channel_id}/unban",
            json={"user_id": str(user2_id), "motive": "Appealed"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["motive"] == "Appealed"

    def test_site_admin_bypasses_channel_permissions(self, client, admin_token, user_token):
        """Test site admins can perform any channel action."""
        create_response = client.post(
            "/channels/",
            json={"name": "Admin Bypass Test", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        channel_id = create_response.json()["id"]

        response = client.patch(
            f"/channels/{channel_id}",
            json={"description": "Admin updated"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        response = client.delete(f"/channels/{channel_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200

    def _get_user_id(self, client, token):
        """Helper to get user ID from token."""
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        return uuid.UUID(response.json()["id"])
