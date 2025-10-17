from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    BASIC = "basic"


ROLE_HIERARCHY = {
    Role.ADMIN: 1,
    Role.BASIC: 2,
}
