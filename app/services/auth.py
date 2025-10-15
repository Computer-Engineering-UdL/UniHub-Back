from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.core import create_access_token, verify_password
from app.crud.user import UserCRUD
from app.schemas import LoginRequest, Token


def authenticate_user(db: Session, login_req: LoginRequest) -> Optional[Token]:
    db_user = UserCRUD.get_by_username(db, login_req.username)
    if db_user is None or not verify_password(login_req.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(
        data={"sub": str(db_user.id), "username": db_user.username, "email": db_user.email, "role": db_user.role}
    )
    return Token(access_token=token, token_type="bearer")


__all__ = ["authenticate_user"]
