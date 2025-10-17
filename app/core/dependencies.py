import uuid
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.literals.users import Role
from app.schemas import TokenData

from .config import settings

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

        token_data = TokenData(id=user_id, username=username, email=email, role=Role(role.lower()))
    except JWTError:
        raise credentials_exception

    return token_data


def require_role(allowed_roles: List[str]):
    """Verify that the user has the required roles"""

    def role_checker(user: TokenData = Depends(get_current_user)) -> TokenData:
        if any(role > user.role for role in allowed_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
        return user

    return role_checker
