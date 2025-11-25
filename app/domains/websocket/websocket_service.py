import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.valkey import valkey_client


class WebSocketService:
    """
    Domain service for handling WebSocket event broadcasting.
    Decoupled from the raw database implementation.
    """

    async def _publish(self, channel: str, event_type: str, data: dict[str, Any]):
        """
        Internal helper to format the message, serialize UUIDs, and publish to Valkey.
        """

        clean_data = {}
        for k, v in data.items():
            if isinstance(v, uuid.UUID):
                clean_data[k] = str(v)
            else:
                clean_data[k] = v

        message = {"type": event_type, "timestamp": datetime.now(timezone.utc).isoformat(), "data": clean_data}

        await valkey_client.publish(channel, message)

    async def send_channel_message(
        self,
        channel_id: uuid.UUID,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        username: Optional[str] = None,
    ):
        await self._publish(
            f"channel:{channel_id}",
            "channel_message",
            {
                "channel_id": channel_id,
                "message_id": message_id,
                "user_id": user_id,
                "username": username,
                "content": content,
            },
        )

    async def send_message_update(self, channel_id: uuid.UUID, message_id: uuid.UUID, content: str):
        await self._publish(
            f"channel:{channel_id}",
            "message_updated",
            {"channel_id": channel_id, "message_id": message_id, "content": content},
        )

    async def send_message_delete(self, channel_id: uuid.UUID, message_id: uuid.UUID):
        await self._publish(
            f"channel:{channel_id}", "message_deleted", {"channel_id": channel_id, "message_id": message_id}
        )

    async def send_message_reply(
        self,
        channel_id: uuid.UUID,
        message_id: uuid.UUID,
        parent_message_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        username: Optional[str] = None,
    ):
        await self._publish(
            f"channel:{channel_id}",
            "message_reply",
            {
                "channel_id": channel_id,
                "message_id": message_id,
                "parent_message_id": parent_message_id,
                "user_id": user_id,
                "username": username,
                "content": content,
            },
        )

    async def send_member_joined(self, channel_id: uuid.UUID, user_id: uuid.UUID, username: Optional[str] = None):
        await self._publish(
            f"channel:{channel_id}",
            "member_joined",
            {"channel_id": channel_id, "user_id": user_id, "username": username},
        )

    async def send_member_left(self, channel_id: uuid.UUID, user_id: uuid.UUID, username: Optional[str] = None):
        await self._publish(
            f"channel:{channel_id}", "member_left", {"channel_id": channel_id, "user_id": user_id, "username": username}
        )

    async def send_member_role_updated(
        self, channel_id: uuid.UUID, user_id: uuid.UUID, new_role: str, username: Optional[str] = None
    ):
        await self._publish(
            f"channel:{channel_id}",
            "member_role_updated",
            {"channel_id": channel_id, "user_id": user_id, "username": username, "new_role": new_role},
        )

    async def send_user_banned(self, channel_id: uuid.UUID, user_id: uuid.UUID, motive: str):
        await self._publish(f"user:{user_id}", "user_banned", {"channel_id": channel_id, "motive": motive})

        await self._publish(
            f"channel:{channel_id}", "user_banned", {"channel_id": channel_id, "user_id": user_id, "motive": motive}
        )

    async def send_user_unbanned(self, channel_id: uuid.UUID, user_id: uuid.UUID, motive: str):
        await self._publish(f"user:{user_id}", "user_unbanned", {"channel_id": channel_id, "motive": motive})
        await self._publish(
            f"channel:{channel_id}", "user_unbanned", {"channel_id": channel_id, "user_id": user_id, "motive": motive}
        )

    async def send_user_kicked(self, channel_id: uuid.UUID, user_id: uuid.UUID):
        await self._publish(f"user:{user_id}", "user_kicked", {"channel_id": channel_id})
        await self._publish(f"channel:{channel_id}", "user_kicked", {"channel_id": channel_id, "user_id": user_id})

    async def send_channel_created(self, channel_id: uuid.UUID, channel_name: str):
        await self._publish("global", "channel_created", {"channel_id": channel_id, "channel_name": channel_name})

    async def send_channel_updated(self, channel_id: uuid.UUID, updated_fields: dict):
        data = {"channel_id": channel_id}
        data.update(updated_fields)

        await self._publish(f"channel:{channel_id}", "channel_updated", data)

    async def send_channel_deleted(self, channel_id: uuid.UUID):
        await self._publish(f"channel:{channel_id}", "channel_deleted", {"channel_id": channel_id})

    async def send_typing_indicator(self, channel_id: uuid.UUID, user_id: uuid.UUID, username: str, is_typing: bool):
        await self._publish(
            f"channel:{channel_id}",
            "user_typing",
            {"channel_id": channel_id, "user_id": user_id, "username": username, "is_typing": is_typing},
        )

    async def send_message_notification(
        self, conversation_id: uuid.UUID, recipient_id: uuid.UUID, sender_id: uuid.UUID, content: str
    ):
        await self._publish(
            f"user:{recipient_id}",
            "message",
            {"conversation_id": conversation_id, "sender_id": sender_id, "content": content},
        )

    async def send_general_notification(self, user_id: uuid.UUID, title: str, message: str):
        await self._publish(f"user:{user_id}", "notification", {"title": title, "message": message})


ws_service = WebSocketService()
