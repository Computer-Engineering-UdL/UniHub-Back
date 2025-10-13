from app.schemas.channel import ChannelBase, ChannelCreate, ChannelRead, ChannelUpdate, MembershipRead
from app.schemas.user import UserCreate, UserList, UserPasswordChange, UserPublic, UserRead

from app.schemas.auth import AuthResponse, LoginRequest  # isort: skip

ChannelRead.model_rebuild()
ChannelCreate.model_rebuild()
ChannelUpdate.model_rebuild()
MembershipRead.model_rebuild()
UserPublic.model_rebuild()
UserRead.model_rebuild()
UserList.model_rebuild()
UserCreate.model_rebuild()
UserPasswordChange.model_rebuild()
AuthResponse.model_rebuild()
LoginRequest.model_rebuild()

__all__ = [
    "ChannelRead",
    "ChannelBase",
    "ChannelCreate",
    "ChannelUpdate",
    "MembershipRead",
    "UserPublic",
    "AuthResponse",
    "UserList",
    "UserCreate",
    "UserRead",
    "UserPasswordChange",
    "LoginRequest",
]
