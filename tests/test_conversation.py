import uuid

import pytest
from fastapi import status


class TestConversationCreate:
    """Tests for creating conversations."""

    def test_create_conversation_success(self, client, user_token, user2_token, db):
        """Test creating a new conversation between two users."""

        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user2_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["user1_id"] is not None
        assert data["user2_id"] is not None
        assert data["created_at"] is not None

    def test_create_conversation_with_initial_message(self, client, user_token, user2_token):
        """Test creating conversation with an initial message."""
        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={
                "other_user_id": user2_id,
                "initial_message": "Hello, is this room still available?",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data

        conv_id = data["id"]
        response = client.get(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        messages = response.json()["messages"]
        assert len(messages) >= 1
        assert messages[0]["content"] == "Hello, is this room still available?"

    def test_create_conversation_with_housing_offer(self, client, user_token, user2_token, db):
        """Test creating conversation linked to a housing offer."""
        from app.models import HousingOfferTableModel

        offer = db.query(HousingOfferTableModel).first()
        if not offer:
            pytest.skip("No housing offers in database")

        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={
                "other_user_id": user2_id,
                "housing_offer_id": str(offer.id),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["housing_offer_id"] == str(offer.id)

    def test_create_conversation_with_self_fails(self, client, user_token):
        """Test that creating conversation with yourself fails."""
        response = client.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
        user_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot create conversation with yourself" in response.json()["detail"]

    def test_create_duplicate_conversation_returns_existing(self, client, user_token, user2_token):
        """Test that creating duplicate conversation returns existing one."""
        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        response1 = client.post(
            "/conversations/",
            json={"other_user_id": user2_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response1.status_code == status.HTTP_201_CREATED
        conv1_id = response1.json()["id"]

        response2 = client.post(
            "/conversations/",
            json={"other_user_id": user2_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response2.status_code == status.HTTP_201_CREATED
        conv2_id = response2.json()["id"]

        assert conv1_id == conv2_id

    def test_create_conversation_unauthorized(self, client, user2_token):
        """Test creating conversation without authentication fails."""
        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user2_id},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestConversationList:
    """Tests for listing conversations."""

    def test_get_my_conversations_empty(self, client, admin_token):
        """Test getting conversations when user has none."""
        response = client.get(
            "/conversations/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_get_my_conversations_with_data(self, client, user_token, user2_token):
        """Test getting conversations after creating some."""

        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        client.post(
            "/conversations/",
            json={"other_user_id": user2_id, "initial_message": "Test message"},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        response = client.get(
            "/conversations/",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        conversations = response.json()
        assert len(conversations) >= 1
        assert conversations[0]["last_message"] is not None

    def test_get_conversations_pagination(self, client, user_token):
        """Test conversation list pagination."""
        response = client.get(
            "/conversations/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        conversations = response.json()
        assert len(conversations) <= 10

    def test_get_conversations_shows_unread_count(self, client, user_token, user2_token):
        """Test that unread message count is included."""

        response = client.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
        user1_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user1_id, "initial_message": "Unread message"},
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        response = client.get(
            "/conversations/",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        conversations = response.json()
        print(conversations)
        assert any(conv["unread_count"] > 0 for conv in conversations)

    def test_get_conversations_unauthorized(self, client):
        """Test getting conversations without authentication fails."""
        response = client.get("/conversations/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestConversationDetail:
    """Tests for getting conversation details."""

    def test_get_conversation_success(self, client, user_token, user2_token):
        """Test getting a specific conversation."""
        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user2_id, "initial_message": "Test"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        conv_id = response.json()["id"]

        response = client.get(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == conv_id
        assert "messages" in data
        assert len(data["messages"]) >= 1

    def test_get_conversation_marks_as_read(self, client, user_token, user2_token):
        """Test that getting conversation marks messages as read."""
        response = client.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
        user1_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user1_id, "initial_message": "Hello"},
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        conv_id = response.json()["id"]

        response = client.get(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        response = client.get(
            "/conversations/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        conversations = response.json()
        conv = next(c for c in conversations if c["id"] == conv_id)
        assert conv["unread_count"] == 0

    def test_get_conversation_not_found(self, client, user_token):
        """Test getting non-existent conversation."""
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/conversations/{fake_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_conversation_not_participant(self, client, user_token, user2_token, admin_token):
        """Test that non-participants cannot access conversation."""
        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user2_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        conv_id = response.json()["id"]

        response = client.get(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestConversationMessages:
    """Tests for sending and retrieving messages."""

    def test_send_message_success(self, client, user_token, user2_token):
        """Test sending a message in a conversation."""
        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user2_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        conv_id = response.json()["id"]

        response = client.post(
            f"/conversations/{conv_id}/messages",
            json={"content": "Hello there!"},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "Hello there!"
        assert data["conversation_id"] == conv_id
        assert data["is_read"] is False

    def test_send_message_updates_last_message_at(self, client, user_token, user2_token):
        """Test that sending message updates conversation timestamp."""
        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user2_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        conv_id = response.json()["id"]
        initial_timestamp = response.json()["last_message_at"]

        response = client.post(
            f"/conversations/{conv_id}/messages",
            json={"content": "Update timestamp"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        response = client.get(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        new_timestamp = response.json()["last_message_at"]
        assert new_timestamp != initial_timestamp

    def test_send_empty_message_fails(self, client, user_token, user2_token):
        """Test sending empty message fails validation."""
        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user2_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        conv_id = response.json()["id"]

        response = client.post(
            f"/conversations/{conv_id}/messages",
            json={"content": ""},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_get_conversation_messages(self, client, user_token, user2_token):
        """Test retrieving messages from a conversation."""
        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user2_id, "initial_message": "First message"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        conv_id = response.json()["id"]

        response = client.get(
            f"/conversations/{conv_id}/messages",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        messages = response.json()
        assert len(messages) >= 1
        assert messages[0]["content"] == "First message"

    def test_get_messages_pagination(self, client, user_token, user2_token):
        """Test message pagination."""
        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user2_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        conv_id = response.json()["id"]

        for i in range(5):
            client.post(
                f"/conversations/{conv_id}/messages",
                json={"content": f"Message {i}"},
                headers={"Authorization": f"Bearer {user_token}"},
            )

        response = client.get(
            f"/conversations/{conv_id}/messages?skip=0&limit=3",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        messages = response.json()
        assert len(messages) <= 3


class TestMarkAsRead:
    """Tests for marking messages as read."""

    def test_mark_conversation_read(self, client, user_token, user2_token):
        """Test marking all messages in conversation as read."""
        response = client.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
        user1_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user1_id, "initial_message": "Unread"},
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        conv_id = response.json()["id"]

        response = client.post(
            f"/conversations/{conv_id}/mark-read",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = client.get(
            "/conversations/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        conversations = response.json()
        conv = next(c for c in conversations if c["id"] == conv_id)
        assert conv["unread_count"] == 0

    def test_mark_read_not_found(self, client, user_token):
        """Test marking non-existent conversation as read."""
        fake_id = str(uuid.uuid4())
        response = client.post(
            f"/conversations/{fake_id}/mark-read",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteConversation:
    """Tests for deleting conversations."""

    def test_delete_conversation_success(self, client, user_token, user2_token):
        """Test deleting a conversation."""
        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user2_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        conv_id = response.json()["id"]

        response = client.delete(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = client.get(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_conversation_not_found(self, client, user_token):
        """Test deleting non-existent conversation."""
        fake_id = str(uuid.uuid4())
        response = client.delete(
            f"/conversations/{fake_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_conversation_cascades_messages(self, client, user_token, user2_token, db):
        """Test that deleting conversation also deletes messages."""
        from app.models import ConversationMessage

        response = client.get("/users/me", headers={"Authorization": f"Bearer {user2_token}"})
        user2_id = response.json()["id"]

        response = client.post(
            "/conversations/",
            json={"other_user_id": user2_id, "initial_message": "To be deleted"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        conv_id = response.json()["id"]

        response = client.delete(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        messages = db.query(ConversationMessage).filter_by(conversation_id=uuid.UUID(conv_id)).all()
        assert len(messages) == 0
