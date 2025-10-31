import uuid
from typing import Any

from fastapi import Depends
from sqlalchemy.orm import Session
from starlette import status
from starlette.exceptions import HTTPException

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.types import TokenData
from app.literals.channels import CHANNEL_ROLE_HIERARCHY, ChannelRole
from app.literals.users import ROLE_HIERARCHY, Role
from app.models import Channel, ChannelMember


def get_channel_permission(min_role: ChannelRole = ChannelRole.USER):
    """Factory to create channel permission checker.
    Args:
        min_role: Minimum channel role required to access
    Raises:
        HTTPException: If user does not have required channel roles
    """

    def permission_checker(
        channel_id: uuid.UUID,
        user: TokenData = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> type[ChannelMember] | None:
        membership = (
            db.query(ChannelMember)
            .filter(ChannelMember.channel_id == channel_id, ChannelMember.user_id == user.id)
            .one_or_none()
        )
        if user.role == Role.ADMIN:
            return membership

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this channel",
            )
        if membership.is_banned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are banned from this channel",
            )
        if CHANNEL_ROLE_HIERARCHY[membership.role] > CHANNEL_ROLE_HIERARCHY[min_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires elevated access")

        return membership

    return permission_checker


def is_channel_member(
    channel_id: uuid.UUID,
    user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> type[ChannelMember] | None:
    """Check if user is a channel member"""
    membership = (
        db.query(ChannelMember)
        .filter(ChannelMember.channel_id == channel_id, ChannelMember.user_id == user.id)
        .one_or_none()
    )
    if user.role == Role.ADMIN:
        return membership

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this channel",
        )

    if membership.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are banned from this channel",
        )

    return membership


def _to_site_role(value: Any) -> Role:
    if isinstance(value, Role):
        return value
    try:
        return Role(str(value))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid role value: {value!r}",
        ) from exc


def _check_site_role_threshold(
    *,
    user_role: Role | None,
    required_min_role: Role | str | Any,
    admin_bypass: bool = True,
) -> None:
    """
    Compare user's SITE role vs the required minimum SITE role for the channel.
    Raise 403 if insufficient. Optionally bypass for site Admin.
    """
    if admin_bypass and user_role == Role.ADMIN:
        return

    effective_role = user_role or Role.BASIC
    required_role = _to_site_role(required_min_role)

    if ROLE_HIERARCHY[effective_role] > ROLE_HIERARCHY[required_role]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient site role for this channel",
        )


def require_site_role_for_channel_read(
    channel_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: TokenData | None = None,
) -> Channel:
    channel: Channel | None = db.query(Channel).filter(Channel.id == channel_id).one_or_none()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

    user_role = user.role if user else None
    _check_site_role_threshold(user_role=user_role, required_min_role=channel.read_min_role)
    return channel


def require_site_role_for_channel_write(
    channel_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user),
) -> Channel:
    channel: Channel | None = db.query(Channel).filter(Channel.id == channel_id).one_or_none()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

    _check_site_role_threshold(user_role=user.role, required_min_role=channel.write_min_role)
    return channel
