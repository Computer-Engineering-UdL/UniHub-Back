from enum import Enum


class Role(str, Enum):
    ADMIN = "Admin"
    SELLER = "Seller"
    RECRUITER = "Recruiter"
    BASIC = "Basic"


ROLE_HIERARCHY = {
    Role.ADMIN: 1,
    Role.SELLER: 2,
    Role.RECRUITER: 2,
    Role.BASIC: 3,
}
