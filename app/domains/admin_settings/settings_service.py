from __future__ import annotations

import datetime
import logging
import smtplib
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.core.valkey import valkey_client
from app.domains.admin_settings.settings_repository import SettingsRepository
from app.schemas.admin_settings import (
    AllSettingsResponse,
    ContentSettingsSchema,
    NotificationSettingsResponse,
    SecuritySettingsSchema,
    SettingsUpdateRequest,
    SettingsUpdateResponse,
    SystemSettingsSchema,
)

logger = logging.getLogger(__name__)

SETTINGS_CACHE_KEY = "admin:settings"
SETTINGS_CACHE_TTL = 300  # 5 minutes


class SettingsService:
    """Service for managing system settings with caching and audit logging."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = SettingsRepository(db)

    async def get_settings(self) -> AllSettingsResponse:
        """
        Get all settings with SMTP password masked.
        Uses cache when available.
        """

        cached = await valkey_client.get(SETTINGS_CACHE_KEY)
        if cached:
            return AllSettingsResponse(**cached)

        settings = self.repository.get_or_create_settings()

        response = self._build_response(settings)

        await valkey_client.set(SETTINGS_CACHE_KEY, response.model_dump(by_alias=True), SETTINGS_CACHE_TTL)

        return response

    async def update_settings(
        self,
        update_request: SettingsUpdateRequest,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> SettingsUpdateResponse:
        """
        Update settings with validation, audit logging, and cache invalidation.
        """

        current_settings = self.repository.get_or_create_settings()
        changes: Dict[str, Any] = {}

        system_data = None
        security_data = None
        content_data = None
        notification_data = None

        if update_request.system:
            system_data = update_request.system.model_dump(by_alias=True)
            changes["system"] = {
                "old": current_settings.system_settings,
                "new": system_data,
            }

        if update_request.security:
            security_data = update_request.security.model_dump(by_alias=True)
            changes["security"] = {
                "old": current_settings.security_settings,
                "new": security_data,
            }

        if update_request.content:
            content_data = update_request.content.model_dump(by_alias=True)
            changes["content"] = {
                "old": current_settings.content_settings,
                "new": content_data,
            }

        if update_request.notifications:
            notification_data = update_request.notifications.model_dump(by_alias=True)

            audit_notification_data = {**notification_data}
            if "smtpPassword" in audit_notification_data and audit_notification_data["smtpPassword"]:
                audit_notification_data["smtpPassword"] = "********"
            old_notifications = {**current_settings.notification_settings}
            if "smtpPassword" in old_notifications:
                old_notifications["smtpPassword"] = "********"
            changes["notifications"] = {
                "old": old_notifications,
                "new": audit_notification_data,
            }

        updated_settings = self.repository.update_settings(
            system=system_data,
            security=security_data,
            content=content_data,
            notifications=notification_data,
        )

        if changes:
            self.repository.create_audit_log(
                admin_id=admin_id,
                changes=changes,
                ip_address=ip_address,
                user_agent=user_agent,
                description="Settings updated via admin API",
            )

        await valkey_client.unset(SETTINGS_CACHE_KEY)

        response = self._build_response(updated_settings)

        return SettingsUpdateResponse(
            message="Settings updated successfully",
            settings=response,
        )

    async def send_test_email(self, recipient: str) -> Dict[str, Any]:
        """
        Send a test email using current SMTP configuration.
        """
        settings = self.repository.get_or_create_settings()
        notification_settings = settings.notification_settings or {}

        smtp_server = notification_settings.get("smtpServer", "")
        smtp_port = notification_settings.get("smtpPort", 587)
        smtp_username = notification_settings.get("smtpUsername", "")
        smtp_password = notification_settings.get("smtpPassword", "")
        email_from = notification_settings.get("emailFrom", "noreply@unihub.smuks.dev")

        if not smtp_server or not smtp_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMTP is not configured. Please configure SMTP settings first.",
            )

        sent_at = datetime.datetime.now(datetime.UTC)

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "UniHub - Email Configuration Test"
            msg["From"] = email_from
            msg["To"] = recipient

            text_content = f"""This is a test email from UniHub Admin Settings.

If you received this email, your SMTP configuration is working correctly.

Sent at: {sent_at.strftime("%Y-%m-%d %H:%M:%S")} UTC
"""
            html_content = f"""
<html>
<body>
<h2>UniHub - Email Configuration Test</h2>
<p>This is a test email from UniHub Admin Settings.</p>
<p>If you received this email, your SMTP configuration is working correctly.</p>
<p><strong>Sent at:</strong> {sent_at.strftime("%Y-%m-%d %H:%M:%S")} UTC</p>
</body>
</html>
"""
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)

            logger.info(f"Test email sent successfully to {recipient}")

            return {
                "message": "Test email sent successfully",
                "recipient": recipient,
                "sentAt": sent_at.isoformat(),
            }

        except smtplib.SMTPAuthenticationError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SMTP authentication failed. Please check your credentials.",
            )
        except smtplib.SMTPException as e:
            logger.error(f"Failed to send test email: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send test email: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Unexpected error sending test email: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while sending the test email.",
            )

    async def clear_cache(self) -> Dict[str, Any]:
        """
        Clear all application caches (Redis/Valkey).
        """
        cleared_at = datetime.datetime.now(datetime.UTC)

        try:
            await valkey_client.client.flushdb()

            logger.info("Cache cleared successfully")

            return {
                "message": "Cache cleared successfully",
                "clearedAt": cleared_at.isoformat(),
                "details": {
                    "redis": True,
                    "applicationCache": True,
                    "cdnCache": False,
                },
            }
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clear cache: {str(e)}",
            )

    def _build_response(self, settings) -> AllSettingsResponse:
        """Build AllSettingsResponse from database model."""
        system_data = settings.system_settings or {}
        security_data = settings.security_settings or {}
        content_data = settings.content_settings or {}
        notification_data = settings.notification_settings or {}

        return AllSettingsResponse(
            system=SystemSettingsSchema(
                maintenance_mode=system_data.get("maintenanceMode", False),
                allow_new_registrations=system_data.get("allowNewRegistrations", True),
                require_email_verification=system_data.get("requireEmailVerification", True),
                max_upload_size_mb=system_data.get("maxUploadSizeMb", 10),
                session_timeout_minutes=system_data.get("sessionTimeoutMinutes", 120),
                default_language=system_data.get("defaultLanguage", "ca"),
                email_notifications=system_data.get("emailNotifications", True),
                push_notifications=system_data.get("pushNotifications", True),
                auto_moderation=system_data.get("autoModeration", False),
                max_images_per_post=system_data.get("maxImagesPerPost", 10),
            ),
            security=SecuritySettingsSchema(
                password_min_length=security_data.get("passwordMinLength", 8),
                password_require_uppercase=security_data.get("passwordRequireUppercase", True),
                password_require_numbers=security_data.get("passwordRequireNumbers", True),
                password_require_special_chars=security_data.get("passwordRequireSpecialChars", False),
                max_login_attempts=security_data.get("maxLoginAttempts", 5),
                account_lockout_minutes=security_data.get("accountLockoutMinutes", 30),
                two_factor_auth_enabled=security_data.get("twoFactorAuthEnabled", False),
            ),
            content=ContentSettingsSchema(
                allow_anonymous_posts=content_data.get("allowAnonymousPosts", False),
                require_post_approval=content_data.get("requirePostApproval", False),
                max_post_length=content_data.get("maxPostLength", 5000),
                allow_external_links=content_data.get("allowExternalLinks", True),
                profanity_filter_enabled=content_data.get("profanityFilterEnabled", True),
                min_report_threshold=content_data.get("minReportThreshold", 3),
            ),
            notifications=NotificationSettingsResponse(
                email_from=notification_data.get("emailFrom", "noreply@unihub.smuks.dev"),
                email_reply_to=notification_data.get("emailReplyTo", "support@unihub.smuks.dev"),
                smtp_server=notification_data.get("smtpServer", "smtp.gmail.com"),
                smtp_port=notification_data.get("smtpPort", 587),
                smtp_username=notification_data.get("smtpUsername", ""),
                smtp_password="********",  # Always mask password in response
            ),
        )
