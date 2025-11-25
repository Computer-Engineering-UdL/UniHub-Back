import asyncio
import uuid

import pytest
from starlette.websockets import WebSocketDisconnect

from app.domains.auth.auth_service import verify_token
from app.domains.websocket.websocket_manager import ws_manager
from app.domains.websocket.websocket_service import ws_service
from app.models import ChannelMember


def test_websocket_connect_success(client, user_token):
    """
    Test that a user can successfully connect with a valid token.
    """
    with client.websocket_connect(f"/ws?token={user_token}") as _:
        pass


def test_websocket_connect_no_token(client):
    """
    Test that connection fails without a token.
    """
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws"):
            pass


def test_websocket_connect_invalid_token(client):
    """
    Test that connection closes with invalid token.
    """
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws?token=invalid_token_string") as websocket:
            websocket.receive_json()


def test_websocket_receive_notification(client, user_token, db):
    """
    Test that the WebSocket receives a message published to Redis via ws_service.
    """

    payload = verify_token(user_token)
    user_id = uuid.UUID(payload.get("sub"))

    with client.websocket_connect(f"/ws?token={user_token}") as websocket:
        notification_data = {"title": "Test", "message": "Hello World"}

        async def send_notif():
            await ws_service.send_general_notification(
                user_id=user_id, title=notification_data["title"], message=notification_data["message"]
            )

        asyncio.get_event_loop().run_until_complete(send_notif())

        data = websocket.receive_json()

        assert data["type"] == "notification"
        assert data["data"]["title"] == "Test"
        assert data["data"]["message"] == "Hello World"


def test_websocket_channel_subscription(client, user_token, db):
    """
    Test that the user automatically subscribes to channels they are a member of.
    Uses seeded data.
    """

    payload = verify_token(user_token)
    user_id = uuid.UUID(payload.get("sub"))

    member_record = db.query(ChannelMember).filter(ChannelMember.user_id == user_id).first()
    if not member_record:
        pytest.fail("Test user is not a member of any seeded channel.")

    channel_id = member_record.channel_id

    with client.websocket_connect(f"/ws?token={user_token}") as websocket:
        msg_id = uuid.uuid4()
        content = "Channel Hello from Tests"

        async def send_channel_msg():
            await ws_service.send_channel_message(
                channel_id=channel_id, message_id=msg_id, user_id=user_id, content=content, username="tester"
            )

        asyncio.get_event_loop().run_until_complete(send_channel_msg())

        data = websocket.receive_json()

        assert data["type"] == "channel_message"
        assert data["data"]["content"] == content
        assert data["data"]["channel_id"] == str(channel_id)


def test_websocket_typing_indicator(client, user_token, db):
    """
    Test sending a typing event from the client and receiving broadcast.
    Uses seeded data.
    """

    payload = verify_token(user_token)
    user_id = uuid.UUID(payload.get("sub"))

    member_record = db.query(ChannelMember).filter(ChannelMember.user_id == user_id).first()
    if not member_record:
        pytest.fail("Test user is not a member of any seeded channel.")

    channel_id = member_record.channel_id

    with client.websocket_connect(f"/ws?token={user_token}") as websocket:
        typing_payload = {"type": "typing", "channel_id": str(channel_id), "is_typing": True}
        websocket.send_json(typing_payload)

        response = websocket.receive_json()

        assert response["type"] == "user_typing"
        assert response["data"]["channel_id"] == str(channel_id)
        assert response["data"]["user_id"] == str(user_id)
        assert response["data"]["is_typing"] is True


def test_websocket_disconnect_cleanup(client, user_token):
    """
    Test that disconnecting cleans up the WebSocketManager state.
    """

    payload = verify_token(user_token)
    user_id_str = payload.get("sub")

    with client.websocket_connect(f"/ws?token={user_token}"):
        assert user_id_str in ws_manager.user_connections

    assert user_id_str not in ws_manager.user_connections
