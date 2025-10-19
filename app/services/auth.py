import re

from fastapi import HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from starlette import status

from app.core import create_access_token, verify_password
from app.core.config import settings
from app.core.security import create_refresh_token
from app.crud.user import UserCRUD
from app.models.user import create_payload_from_user
from app.schemas import LoginRequest, Token


def authenticate_user(db: Session, login_req: LoginRequest) -> Token:
    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if re.match(email_pattern, login_req.username):
        db_user = UserCRUD.get_by_email(db, login_req.username)
    else:
        db_user = UserCRUD.get_by_username(db, login_req.username)
    if db_user is None or not verify_password(login_req.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    data = create_payload_from_user(db_user)
    token = create_access_token(data=data)
    refresh_token = create_refresh_token(data=data)
    return Token(access_token=token, refresh_token=refresh_token, token_type="bearer")


def verify_token(token: str, expected_type: str = None) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        username = payload.get("username")
        email = payload.get("email")
        role = payload.get("role")
        token_type = payload.get("type")

        if user_id is None or username is None or email is None or role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

        if expected_type and token_type != expected_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Expected {expected_type} token")

        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


__all__ = ["authenticate_user", "verify_token"]
