import uuid
from typing import List

from sqlalchemy.orm import Session

from app.domains.channel import ChannelRepository
from app.domains.websocket.websocket_service import ws_service
from app.models import ChannelMember
from app.models.user import User


class WebSocketConnectionService:
    """
    Handles database interactions required during the WebSocket lifecycle.
    """

    def __init__(self, db: Session):
        self.db = db

        self.channel_repo = ChannelRepository(self.db)

    def get_user_channel_subscriptions(self, user_id: uuid.UUID) -> List[str]:
        """
        Fetch all channels the user is a member of to subscribe them to Redis topics.
        Returns a list of strings like ["channel:{uuid}", "channel:{uuid}"]
        """

        memberships = (
            self.db.query(ChannelMember)
            .filter(ChannelMember.user_id == user_id)
            .filter(ChannelMember.is_banned.is_(False))
            .all()
        )

        channel_ids = [m.channel_id for m in memberships]

        topics = [f"channel:{cid}" for cid in channel_ids]
        return topics

    async def handle_client_message(self, data: dict, user_id: uuid.UUID):
        """
        Process incoming messages sent directly via WebSocket (not HTTP).
        Example: Typing indicators, Online status toggles.
        """
        event_type = data.get("type")

        if event_type == "typing":
            await self._handle_typing_event(data, user_id)

    async def _handle_typing_event(self, data: dict, user_id: uuid.UUID):
        """
        Broadcasts a typing indicator to the channel.
        """
        channel_id_str = data.get("channel_id")
        is_typing = data.get("is_typing", False)

        if not channel_id_str:
            return

        try:
            channel_id = uuid.UUID(channel_id_str)

            user = self.db.query(User).filter(User.id == user_id).first()
            username = user.username if user else "Unknown"

            await ws_service.send_typing_indicator(
                channel_id=channel_id, user_id=user_id, username=username, is_typing=is_typing
            )
        except ValueError:
            pass
        except Exception as e:
            print(f"Error handling typing event: {e}")
