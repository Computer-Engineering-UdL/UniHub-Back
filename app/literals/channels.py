from enum import Enum
from typing import Literal

ChannelType = Literal["public", "private", "announcement"]


class ChannelRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"


CHANNEL_ROLE_HIERARCHY = {
    ChannelRole.ADMIN: 1,
    ChannelRole.MODERATOR: 2,
    ChannelRole.USER: 3,
}
