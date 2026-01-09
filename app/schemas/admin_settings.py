from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(word.capitalize() for word in components[1:])


class SystemSettingsSchema(BaseModel):
    """System configuration settings."""

    maintenance_mode: bool = False
    allow_new_registrations: bool = True
    require_email_verification: bool = True
    max_upload_size_mb: int = Field(default=10, ge=1, le=100)
    session_timeout_minutes: int = Field(default=120, ge=5, le=1440)
    default_language: Literal["ca", "es", "en"] = "ca"
    email_notifications: bool = True
    push_notifications: bool = True
    auto_moderation: bool = False
    max_images_per_post: int = Field(default=10, ge=1, le=20)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class SecuritySettingsSchema(BaseModel):
    """Security and authentication settings."""

    password_min_length: int = Field(default=8, ge=6, le=20)
    password_require_uppercase: bool = True
    password_require_numbers: bool = True
    password_require_special_chars: bool = False
    max_login_attempts: int = Field(default=5, ge=3, le=10)
    account_lockout_minutes: int = Field(default=30, ge=5, le=1440)
    two_factor_auth_enabled: bool = False

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class ContentSettingsSchema(BaseModel):
    """Content moderation settings."""

    allow_anonymous_posts: bool = False
    require_post_approval: bool = False
    max_post_length: int = Field(default=5000, ge=100, le=10000)
    allow_external_links: bool = True
    profanity_filter_enabled: bool = True
    min_report_threshold: int = Field(default=3, ge=1, le=10)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class NotificationSettingsSchema(BaseModel):
    """Email/SMTP notification settings."""

    email_from: str = "noreply@unihub.smuks.dev"
    email_reply_to: str = "support@unihub.smuks.dev"
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = ""
    smtp_password: str = ""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class NotificationSettingsResponse(BaseModel):
    """Notification settings for GET response (password masked)."""

    email_from: str
    email_reply_to: str
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str = "********"

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class AllSettingsResponse(BaseModel):
    """Complete settings response for GET /admin/settings."""

    system: SystemSettingsSchema
    security: SecuritySettingsSchema
    content: ContentSettingsSchema
    notifications: NotificationSettingsResponse

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class SettingsUpdateRequest(BaseModel):
    """Request body for PUT /admin/settings - all fields optional."""

    system: Optional[SystemSettingsSchema] = None
    security: Optional[SecuritySettingsSchema] = None
    content: Optional[ContentSettingsSchema] = None
    notifications: Optional[NotificationSettingsSchema] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class SettingsUpdateResponse(BaseModel):
    """Response for PUT /admin/settings."""

    message: str = "Settings updated successfully"
    settings: AllSettingsResponse

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class TestEmailRequest(BaseModel):
    """Request body for POST /admin/settings/test-email."""

    email: EmailStr

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class TestEmailResponse(BaseModel):
    """Response for POST /admin/settings/test-email."""

    message: str = "Test email sent successfully"
    recipient: str
    sent_at: datetime

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class CacheClearDetails(BaseModel):
    """Details of what caches were cleared."""

    redis: bool = True
    application_cache: bool = True
    cdn_cache: bool = False

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class CacheClearResponse(BaseModel):
    """Response for POST /admin/cache/clear."""

    message: str = "Cache cleared successfully"
    cleared_at: datetime
    details: CacheClearDetails

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


__all__ = [
    "SystemSettingsSchema",
    "SecuritySettingsSchema",
    "ContentSettingsSchema",
    "NotificationSettingsSchema",
    "NotificationSettingsResponse",
    "AllSettingsResponse",
    "SettingsUpdateRequest",
    "SettingsUpdateResponse",
    "TestEmailRequest",
    "TestEmailResponse",
    "CacheClearDetails",
    "CacheClearResponse",
]
