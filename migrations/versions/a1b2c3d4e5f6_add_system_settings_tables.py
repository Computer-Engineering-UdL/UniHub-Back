"""add_system_settings_tables

Revision ID: a1b2c3d4e5f6
Revises: ec291f746949
Create Date: 2026-01-04 18:27:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "ec291f746949"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Default settings values
DEFAULT_SYSTEM_SETTINGS = {
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

DEFAULT_SECURITY_SETTINGS = {
    "passwordMinLength": 8,
    "passwordRequireUppercase": True,
    "passwordRequireNumbers": True,
    "passwordRequireSpecialChars": False,
    "maxLoginAttempts": 5,
    "accountLockoutMinutes": 30,
    "twoFactorAuthEnabled": False,
}

DEFAULT_CONTENT_SETTINGS = {
    "allowAnonymousPosts": False,
    "requirePostApproval": False,
    "maxPostLength": 5000,
    "allowExternalLinks": True,
    "profanityFilterEnabled": True,
    "minReportThreshold": 3,
}

DEFAULT_NOTIFICATION_SETTINGS = {
    "emailFrom": "noreply@unihub.smuks.dev",
    "emailReplyTo": "support@unihub.smuks.dev",
    "smtpServer": "smtp.gmail.com",
    "smtpPort": 587,
    "smtpUsername": "",
    "smtpPassword": "",
}


def upgrade() -> None:
    # Create system_settings table
    op.create_table(
        "system_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("system_settings", JSONB(), nullable=False, server_default="{}"),
        sa.Column("security_settings", JSONB(), nullable=False, server_default="{}"),
        sa.Column("content_settings", JSONB(), nullable=False, server_default="{}"),
        sa.Column("notification_settings", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create settings_audit_log table
    op.create_table(
        "settings_audit_log",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("admin_id", sa.UUID(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("changes", JSONB(), nullable=False, server_default="{}"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["admin_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index on changed_at for efficient querying
    op.create_index(
        "ix_settings_audit_log_changed_at",
        "settings_audit_log",
        ["changed_at"],
    )

    # Insert default settings row
    import uuid

    settings_id = str(uuid.uuid4())
    system_settings_json = (
        str(DEFAULT_SYSTEM_SETTINGS).replace("'", '"').replace("True", "true").replace("False", "false")
    )
    security_settings_json = (
        str(DEFAULT_SECURITY_SETTINGS).replace("'", '"').replace("True", "true").replace("False", "false")
    )
    content_settings_json = (
        str(DEFAULT_CONTENT_SETTINGS).replace("'", '"').replace("True", "true").replace("False", "false")
    )
    notification_settings_json = (
        str(DEFAULT_NOTIFICATION_SETTINGS).replace("'", '"').replace("True", "true").replace("False", "false")
    )

    op.execute(
        f"""
        INSERT INTO system_settings (
            id,
            system_settings,
            security_settings,
            content_settings,
            notification_settings,
            created_at,
            updated_at
        )
        VALUES (
            '{settings_id}'::uuid,
            '{system_settings_json}'::jsonb,
            '{security_settings_json}'::jsonb,
            '{content_settings_json}'::jsonb,
            '{notification_settings_json}'::jsonb,
            NOW(),
            NOW()
        )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_settings_audit_log_changed_at")
    op.drop_table("settings_audit_log")
    op.drop_table("system_settings")
