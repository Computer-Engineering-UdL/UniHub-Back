from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.system_settings import SettingsAuditLog, SystemSettings


class SettingsRepository:
    """Repository for CRUD operations on system settings."""

    def __init__(self, db: Session):
        self.db = db

    def get_settings(self) -> Optional[SystemSettings]:
        """Get the singleton settings row."""
        return self.db.query(SystemSettings).first()

    def get_or_create_settings(self) -> SystemSettings:
        """Get existing settings or create with defaults."""
        settings = self.get_settings()
        if not settings:
            settings = SystemSettings(
                id=uuid.uuid4(),
                system_settings=self._default_system_settings(),
                security_settings=self._default_security_settings(),
                content_settings=self._default_content_settings(),
                notification_settings=self._default_notification_settings(),
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        return settings

    def update_settings(
        self,
        system: Optional[Dict[str, Any]] = None,
        security: Optional[Dict[str, Any]] = None,
        content: Optional[Dict[str, Any]] = None,
        notifications: Optional[Dict[str, Any]] = None,
    ) -> SystemSettings:
        """Update settings - merges provided values with existing."""
        settings = self.get_or_create_settings()

        if system is not None:
            current = dict(settings.system_settings or {})
            current.update(system)
            settings.system_settings = current

        if security is not None:
            current = dict(settings.security_settings or {})
            current.update(security)
            settings.security_settings = current

        if content is not None:
            current = dict(settings.content_settings or {})
            current.update(content)
            settings.content_settings = current

        if notifications is not None:
            current = dict(settings.notification_settings or {})
            # Only update password if a new one was provided and it's not masked
            if notifications.get("smtpPassword") == "********":
                notifications.pop("smtpPassword", None)
            current.update(notifications)
            settings.notification_settings = current

        self.db.commit()
        self.db.refresh(settings)
        return settings

    def create_audit_log(
        self,
        admin_id: uuid.UUID,
        changes: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SettingsAuditLog:
        """Create an audit log entry for settings changes."""
        audit_log = SettingsAuditLog(
            id=uuid.uuid4(),
            admin_id=admin_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            description=description,
        )
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log

    @staticmethod
    def _default_system_settings() -> Dict[str, Any]:
        return {
            "maintenanceMode": False,
            "allowNewRegistrations": True,
            "requireEmailVerification": True,
            "maxUploadSizeMb": 10,
            "sessionTimeoutMinutes": 120,
            "defaultLanguage": "ca",
            "emailNotifications": True,
            "pushNotifications": True,
            "autoModeration": False,
            "maxImagesPerPost": 10,
        }

    @staticmethod
    def _default_security_settings() -> Dict[str, Any]:
        return {
            "passwordMinLength": 8,
            "passwordRequireUppercase": True,
            "passwordRequireNumbers": True,
            "passwordRequireSpecialChars": False,
            "maxLoginAttempts": 5,
            "accountLockoutMinutes": 30,
            "twoFactorAuthEnabled": False,
        }

    @staticmethod
    def _default_content_settings() -> Dict[str, Any]:
        return {
            "allowAnonymousPosts": False,
            "requirePostApproval": False,
            "maxPostLength": 5000,
            "allowExternalLinks": True,
            "profanityFilterEnabled": True,
            "minReportThreshold": 3,
        }

    @staticmethod
    def _default_notification_settings() -> Dict[str, Any]:
        return {
            "emailFrom": "noreply@unihub.smuks.dev",
            "emailReplyTo": "support@unihub.smuks.dev",
            "smtpServer": "smtp.gmail.com",
            "smtpPort": 587,
            "smtpUsername": "",
            "smtpPassword": "",
        }
