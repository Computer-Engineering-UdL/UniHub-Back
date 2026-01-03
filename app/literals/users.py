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


class OnboardingStep(str, Enum):
    NOT_STARTED = "not_started"
    PERSONAL_INFO = "personal_info"
    ACADEMIC_INFO = "academic_info"
    PREFERENCES = "preferences"
    COMPLETED = "completed"
