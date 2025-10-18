import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.literals.users import ROLE_HIERARCHY, Role
from app.schemas import TokenData

from ..crud.channel import ChannelCRUD
from ..literals.channels import CHANNEL_ROLE_HIERARCHY, ChannelRole
from ..models import ChannelMember
from .config import settings
from .database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_VERSION}/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Validate JWT token and return current user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: uuid.UUID = payload.get("sub")
        username: str = payload.get("username")
        email: str = payload.get("email")
        role: Role = payload.get("role")

        if user_id is None:
            raise credentials_exception

        token_data = TokenData(id=user_id, username=username, email=email, role=role)
    except JWTError:
        raise credentials_exception

    return token_data


def require_role(min_role: Role):
    """Verify that the user has the required roles

    Args:
        min_role: Minimum role required to access
    Raises:
        HTTPException: If user does not have required roles
    """

    def role_checker(user: TokenData = Depends(get_current_user)) -> TokenData:
        if ROLE_HIERARCHY[user.role] > ROLE_HIERARCHY[min_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires elevated access")
        return user

    return role_checker


def get_channel_permission(min_role: ChannelRole = ChannelRole.USER):
    """Factory to create channel permission checker.
    Args:
        min_role: Minimum channel role required to access
    Raises:
        HTTPException: If user does not have required channel roles
    """

    def permission_checker(
        channel_id: uuid.UUID, user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> ChannelMember:
        if user.role == Role.ADMIN:
            membership = ChannelCRUD.get_member(db, channel_id, user.id)
            return membership

        membership = ChannelCRUD.get_member(db, channel_id, user.id)
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this channel")
        if CHANNEL_ROLE_HIERARCHY[membership.role] > CHANNEL_ROLE_HIERARCHY[min_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires elevated access")

        return membership

    return permission_checker


def is_channel_member(
    channel_id: uuid.UUID, user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)
) -> ChannelMember:
    """Check if user is a channel member"""
    if user.role == Role.ADMIN:
        membership = ChannelCRUD.get_member(db, channel_id, user.id)
        return membership

    membership = ChannelCRUD.get_member(db, channel_id, user.id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this channel")

    return membership
