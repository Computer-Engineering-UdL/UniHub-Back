from app.models.channel import Channel, ChannelTableModel, channel_members
from app.models.housing_offer import HousingOffer, HousingOfferTableModel
from app.models.message import Message, MessageTableModel
from app.models.user import User, UserInDB, UserPublic, UserTableModel

from app.models.auth import AuthResponse, LoginRequest  # isort: skip

User.model_rebuild()
Channel.model_rebuild()
Message.model_rebuild()

__all__ = [
    "User",
    "UserInDB",
    "UserPublic",
    "UserTableModel",
    "LoginRequest",
    "AuthResponse",
    "Message",
    "MessageTableModel",
    "HousingOffer",
    "HousingOfferTableModel",
    "channel_members",
    "ChannelTableModel",
    "Channel",
]
