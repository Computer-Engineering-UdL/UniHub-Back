from app.schemas.channel import ChannelBase, ChannelCreate, ChannelRead, ChannelUpdate, MembershipRead
from app.schemas.user import UserInDB, UserPublic

from app.schemas.auth import AuthResponse, LoginRequest  # isort: skip

ChannelRead.model_rebuild()
ChannelCreate.model_rebuild()
ChannelUpdate.model_rebuild()
MembershipRead.model_rebuild()
UserPublic.model_rebuild()
UserInDB.model_rebuild()
AuthResponse.model_rebuild()
LoginRequest.model_rebuild()

__all__ = [
    "ChannelRead",
    "ChannelBase",
    "ChannelCreate",
    "ChannelUpdate",
    "MembershipRead",
    "UserPublic",
    "UserInDB",
    "AuthResponse",
    "LoginRequest",
]
