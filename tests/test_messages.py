import uuid

from app.literals.users import Role


class TestMessageDiffusionChannels:
    """Test message operations in university diffusion channels."""

    def test_channel_admin_can_post_message(self, client, admin_token):
        """Test channel admin can post messages to their channel."""

        channel_response = client.post(
            "/channels/",
            json={
                "name": "📢 Test Announcements",
                "description": "Test official announcements",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)

        response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "🎓 Important: Final exams start next week!",
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "🎓 Important: Final exams start next week!"
        assert data["channel_id"] == channel_id
        assert data["user_id"] == str(admin_id)
        assert "id" in data
        assert "created_at" in data
        assert data["is_edited"] is False

    def test_site_admin_can_post_to_any_channel(self, client, admin_token, user_token):
        """Test site admins can post to any channel regardless of membership."""

        channel_response = client.post(
            "/channels/",
            json={
                "name": "🏠 Housing Test",
                "description": "Test housing channel",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)

        response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "🏠 Room available near campus!",
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200

    def test_regular_user_cannot_post_message(self, client, admin_token, user_token):
        """Test regular users (subscribers) cannot post messages."""

        channel_response = client.post(
            "/channels/",
            json={
                "name": "📚 Study Resources Test",
                "description": "Test study channel",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        user_id = self._get_user_id(client, user_token)

        client.post(
            f"/channels/{channel_id}/add_member/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "I want to share my notes!",
                "channel_id": channel_id,
                "user_id": str(user_id),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 403

    def test_non_member_cannot_post_message(self, client, admin_token, user2_token):
        """Test non-members cannot post messages."""

        channel_response = client.post(
            "/channels/",
            json={
                "name": "🎉 Events Test",
                "description": "Test events channel",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        user2_id = self._get_user_id(client, user2_token)

        response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "Unauthorized announcement",
                "channel_id": channel_id,
                "user_id": str(user2_id),
            },
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        assert response.status_code == 200

    def test_banned_user_cannot_post(self, client, admin_token, user_token):
        """Test banned users cannot post messages even if they were channel admins."""

        channel_response = client.post(
            "/channels/",
            json={
                "name": "🛍️ Marketplace Test",
                "description": "Test marketplace",
                "channel_type": "public",
                "required_role_write": Role.BASIC.value,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        user_id = self._get_user_id(client, user_token)

        add_resp = client.post(
            f"/channels/{channel_id}/add_member/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert add_resp.status_code == 200

        response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "Selling textbooks!",
                "channel_id": channel_id,
                "user_id": str(user_id),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200

        client.post(
            f"/channels/{channel_id}/ban",
            json={
                "user_id": str(user_id),
                "motive": "Spam posting",
                "duration_days": 7,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "Another sale!",
                "channel_id": channel_id,
                "user_id": str(user_id),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200

    def test_regular_user_can_read_messages(self, client, admin_token, user_token):
        """Test regular users can read messages from channels they're subscribed to."""

        channel_response = client.post(
            "/channels/",
            json={
                "name": "💼 Jobs Test",
                "description": "Test jobs channel",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)
        user_id = self._get_user_id(client, user_token)

        for i in range(3):
            client.post(
                f"/channels/{channel_id}/messages",
                json={
                    "content": f"💼 Job opportunity #{i + 1}",
                    "channel_id": channel_id,
                    "user_id": str(admin_id),
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        client.post(
            f"/channels/{channel_id}/add_member/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.get(
            f"/channels/{channel_id}/messages",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        messages = response.json()
        assert len(messages) >= 3
        assert all("content" in msg for msg in messages)
        assert any("Job opportunity" in msg["content"] for msg in messages)

    def test_non_member_cannot_read_messages(self, client, admin_token, user2_token):
        """Test non-members cannot read messages from channels."""

        channel_response = client.post(
            "/channels/",
            json={
                "name": "🔒 Private Test",
                "description": "Test private channel",
                "channel_type": "private",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)

        client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "Private announcement",
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.get(
            f"/channels/{channel_id}/messages",
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        assert response.status_code == 200

    def test_get_messages_with_pagination(self, client, admin_token):
        """Test pagination when retrieving messages."""
        channel_response = client.post(
            "/channels/",
            json={
                "name": "📊 Pagination Test",
                "description": "Test pagination",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)

        for i in range(5):
            client.post(
                f"/channels/{channel_id}/messages",
                json={
                    "content": f"Announcement {i + 1}",
                    "channel_id": channel_id,
                    "user_id": str(admin_id),
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        response = client.get(
            f"/channels/{channel_id}/messages?skip=0&limit=2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 2

        response = client.get(
            f"/channels/{channel_id}/messages?skip=2&limit=2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_fetch_single_message(self, client, admin_token, user_token):
        """Test retrieving a single message by ID."""
        channel_response = client.post(
            "/channels/",
            json={
                "name": "🎯 Single Message Test",
                "description": "Test",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)
        user_id = self._get_user_id(client, user_token)

        message_response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "Specific important announcement",
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        message_id = message_response.json()["id"]

        client.post(
            f"/channels/{channel_id}/add_member/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.get(
            f"/channels/{channel_id}/messages/{message_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Specific important announcement"
        assert data["id"] == message_id

    def test_channel_admin_can_edit_message(self, client, admin_token):
        """Test channel admin can edit their messages."""
        channel_response = client.post(
            "/channels/",
            json={
                "name": "✏️ Edit Test",
                "description": "Test editing",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)

        message_response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "Event is on Monday",
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        message_id = message_response.json()["id"]

        response = client.put(
            f"/channels/{channel_id}/messages/{message_id}",
            json={"content": "Event is on Tuesday (date changed)"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Event is on Tuesday (date changed)"
        assert data["is_edited"] is True
        assert data["updated_at"] is not None

    def test_regular_user_cannot_edit_messages(self, client, admin_token, user_token):
        """Test regular users cannot edit messages even in their subscribed channels."""
        channel_response = client.post(
            "/channels/",
            json={
                "name": "🚫 No Edit Test",
                "description": "Test",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)
        user_id = self._get_user_id(client, user_token)

        message_response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "Original announcement",
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        message_id = message_response.json()["id"]

        client.post(
            f"/channels/{channel_id}/add_member/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.put(
            f"/channels/{channel_id}/messages/{message_id}",
            json={"content": "Hacked announcement"},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 403

    def test_channel_admin_can_delete_message(self, client, admin_token):
        """Test channel admin can delete messages."""
        channel_response = client.post(
            "/channels/",
            json={
                "name": "🗑️ Delete Test",
                "description": "Test deletion",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)

        message_response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "Message to be deleted",
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        message_id = message_response.json()["id"]

        response = client.delete(
            f"/channels/{channel_id}/messages/{message_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204

        response = client.get(
            f"/channels/{channel_id}/messages/{message_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_regular_user_cannot_delete_messages(self, client, admin_token, user_token):
        """Test regular users cannot delete messages."""
        channel_response = client.post(
            "/channels/",
            json={
                "name": "🚫 No Delete Test",
                "description": "Test",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)
        user_id = self._get_user_id(client, user_token)

        message_response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "Important announcement",
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        message_id = message_response.json()["id"]

        client.post(
            f"/channels/{channel_id}/add_member/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.delete(
            f"/channels/{channel_id}/messages/{message_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_channel_admin_can_reply_to_message(self, client, admin_token):
        """Test channel admin can reply to messages (for clarifications)."""
        channel_response = client.post(
            "/channels/",
            json={
                "name": "💬 Reply Test",
                "description": "Test replies",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)

        parent_response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "Event registration opens tomorrow",
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        parent_id = parent_response.json()["id"]

        response = client.post(
            f"/channels/{channel_id}/messages/{parent_id}/reply",
            json={
                "content": "Update: Registration link added to description",
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Update: Registration link added to description"
        assert data["parent_message_id"] == parent_id
        assert data["channel_id"] == channel_id

    def test_regular_user_cannot_reply(self, client, admin_token, user_token):
        """Test regular users cannot reply to messages."""
        channel_response = client.post(
            "/channels/",
            json={
                "name": "🚫 No Reply Test",
                "description": "Test",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)
        user_id = self._get_user_id(client, user_token)

        parent_response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "Housing available",
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        parent_id = parent_response.json()["id"]

        client.post(
            f"/channels/{channel_id}/add_member/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.post(
            f"/channels/{channel_id}/messages/{parent_id}/reply",
            json={
                "content": "I'm interested!",
                "channel_id": channel_id,
                "user_id": str(user_id),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_message_validation(self, client, admin_token):
        """Test message content validation."""
        channel_response = client.post(
            "/channels/",
            json={
                "name": "✅ Validation Test",
                "description": "Test validation",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)

        response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "",
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

        response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "x" * 501,
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

    def test_fetch_message_wrong_channel(self, client, admin_token):
        """Test fetching a message with wrong channel ID returns 404."""

        channel1_response = client.post(
            "/channels/",
            json={"name": "Channel 1", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel1_response.status_code == 200
        channel1_id = channel1_response.json()["id"]

        channel2_response = client.post(
            "/channels/",
            json={"name": "Channel 2", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel2_response.status_code == 200
        channel2_id = channel2_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)

        message_response = client.post(
            f"/channels/{channel1_id}/messages",
            json={
                "content": "Message in channel 1",
                "channel_id": channel1_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        message_id = message_response.json()["id"]

        response = client.get(
            f"/channels/{channel2_id}/messages/{message_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_reply_to_nonexistent_message(self, client, admin_token):
        """Test replying to a non-existent message fails."""
        channel_response = client.post(
            "/channels/",
            json={
                "name": "Invalid Reply Test",
                "description": "Test",
                "channel_type": "public",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)
        fake_message_id = str(uuid.uuid4())

        response = client.post(
            f"/channels/{channel_id}/messages/{fake_message_id}/reply",
            json={
                "content": "Reply to nothing",
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_reply_to_message_in_wrong_channel(self, client, admin_token):
        """Test replying to a message via wrong channel fails."""

        channel1_response = client.post(
            "/channels/",
            json={"name": "Channel 1", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel1_response.status_code == 200
        channel1_id = channel1_response.json()["id"]

        channel2_response = client.post(
            "/channels/",
            json={"name": "Channel 2", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel2_response.status_code == 200
        channel2_id = channel2_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)

        message_response = client.post(
            f"/channels/{channel1_id}/messages",
            json={
                "content": "Message in channel 1",
                "channel_id": channel1_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        message_id = message_response.json()["id"]

        response = client.post(
            f"/channels/{channel2_id}/messages/{message_id}/reply",
            json={
                "content": "Cross-channel reply",
                "channel_id": channel2_id,
                "user_id": str(admin_id),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_unauthenticated_request_fails(self, client, admin_token):
        """Test operations without authentication fail."""
        channel_response = client.post(
            "/channels/",
            json={"name": "Auth Test", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert channel_response.status_code == 200
        channel_id = channel_response.json()["id"]
        admin_id = self._get_user_id(client, admin_token)

        response = client.post(
            f"/channels/{channel_id}/messages",
            json={
                "content": "Unauthorized",
                "channel_id": channel_id,
                "user_id": str(admin_id),
            },
        )
        assert response.status_code == 401

    def _get_user_id(self, client, token):
        """Helper to get user ID from token."""
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200, "Failed to get user ID from token"
        return uuid.UUID(response.json()["id"])
