from enum import Enum


class ReportStatus(str, Enum):
    PENDING = "pending"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ReportPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportCategory(str, Enum):
    HOUSING = "housing"
    MARKETPLACE = "marketplace"
    CHANNELS = "channels"
    MESSAGES = "messages"
    SERVICES = "services"
    USER = "user"


class ReportReason(str, Enum):
    SCAM_FRAUD = "scam_fraud"
    HARASSMENT = "harassment"
    SPAM = "spam"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    FAKE_LISTING = "fake_listing"
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    OTHER = "other"
