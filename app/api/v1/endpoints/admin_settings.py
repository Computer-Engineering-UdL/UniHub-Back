from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from starlette import status

from app.api.dependencies import require_role
from app.core.database import get_db
from app.core.types import TokenData
from app.domains.admin_settings.settings_service import SettingsService
from app.literals.users import Role
from app.schemas.admin_settings import (
    AllSettingsResponse,
    CacheClearResponse,
    SettingsUpdateRequest,
    SettingsUpdateResponse,
    TestEmailRequest,
    TestEmailResponse,
)

router = APIRouter()


def get_settings_service(db: Session = Depends(get_db)) -> SettingsService:
    """Dependency to inject SettingsService."""
    return SettingsService(db)


@router.get(
    "/settings",
    response_model=AllSettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get system settings",
    response_description="Returns current system configuration with masked SMTP password.",
)
async def get_settings(
    service: SettingsService = Depends(get_settings_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Get all system settings.

    **Requires Admin role.**

    Returns system, security, content, and notification settings.
    SMTP password is always masked in the response.
    """
    return await service.get_settings()


@router.put(
    "/settings",
    response_model=SettingsUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update system settings",
    response_description="Returns updated settings.",
)
async def update_settings(
    request: Request,
    update_data: SettingsUpdateRequest,
    service: SettingsService = Depends(get_settings_service),
    current_user: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Update system settings.

    **Requires Admin role.**

    Only send the fields that need to be changed.
    All changes are logged for audit purposes.
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    return await service.update_settings(
        update_request=update_data,
        admin_id=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


@router.post(
    "/settings/test-email",
    response_model=TestEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send test email",
    response_description="Returns confirmation of sent email.",
)
async def send_test_email(
    email_request: TestEmailRequest,
    service: SettingsService = Depends(get_settings_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Send a test email using current SMTP configuration.

    **Requires Admin role.**

    Use this to verify that SMTP settings are correctly configured.
    """
    result = await service.send_test_email(str(email_request.email))
    return TestEmailResponse(
        message=result["message"],
        recipient=result["recipient"],
        sent_at=result["sentAt"],
    )


@router.post(
    "/cache/clear",
    response_model=CacheClearResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear system cache",
    response_description="Returns confirmation of cleared cache.",
)
async def clear_cache(
    service: SettingsService = Depends(get_settings_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Clear all system cache (Redis/Valkey).

    **Requires Admin role.**

    This will clear all cached data including user sessions,
    rate limit counters, and cached settings.
    """
    result = await service.clear_cache()
    return CacheClearResponse(
        message=result["message"],
        cleared_at=result["clearedAt"],
        details=result["details"],
    )
