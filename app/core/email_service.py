from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending transactional emails.
    """

    def __init__(self):
        self._smtp_configured = bool(settings.SMTP_HOST and settings.SMTP_USER)

        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email. Returns True if successful."""
        if not self._smtp_configured:
            logger.info(f"[EMAIL DEV MODE] To: {to_email}\nSubject: {subject}\nContent: {text_content or html_content}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to_email

            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_verification_email(self, to_email: str, token: str, username: str) -> bool:
        """Send email verification link."""
        verification_link = f"{settings.FRONTEND_URL}/verify?token={token}"
        subject = "Verify your UniRoom email address"

        template = self.env.get_template("verification_email.html")
        html_content = template.render(
            username=username,
            verification_link=verification_link,
            expire_hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS,
        )

        text_content = f"""
        Welcome to UniRoom, {username}!

        Please verify your email address by visiting:
        {verification_link}

        This link expires in {settings.VERIFICATION_TOKEN_EXPIRE_HOURS} hours.

        If you didn't create an account, you can safely ignore this email.
        """

        return self._send_email(to_email, subject, html_content, text_content)

    def send_password_reset_email(self, to_email: str, token: str, username: str) -> bool:
        """Send password reset link."""

        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        subject = "Reset your UniRoom password"

        template = self.env.get_template("password_reset.html")
        html_content = template.render(
            username=username, reset_link=reset_link, expire_hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
        )

        text_content = f"""
        Password Reset Request

        Hi {username},

        We received a request to reset your password. Visit this link to set a new password:
        {reset_link}

        This link expires in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hour(s).

        If you didn't request this, you can safely ignore this email. Your password won't be changed.
        """

        return self._send_email(to_email, subject, html_content, text_content)


email_service = EmailService()
