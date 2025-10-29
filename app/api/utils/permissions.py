import uuid

from fastapi import Depends
from sqlalchemy.orm import Session
from starlette import status
from starlette.exceptions import HTTPException

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.types import TokenData
from app.literals.channels import CHANNEL_ROLE_HIERARCHY, ChannelRole
from app.literals.users import Role
from app.models import ChannelMember


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
