import uuid

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status

from app.core import create_access_token
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_refresh_token
from app.crud.user import UserCRUD
from app.models import create_payload_from_user
from app.schemas import LoginRequest, Token, TokenData
from app.services import authenticate_user
from app.services.auth import verify_token

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 compatible token endpoint.
    Form data expects 'username' and 'password' fields.
    """
    login_request = LoginRequest(username=form_data.username, password=form_data.password)

    return authenticate_user(db, login_request)


@router.post("/refresh", response_model=Token)
async def refresh(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    payload = verify_token(refresh_token, expected_type="refresh")
    db_user = UserCRUD.get_by_id(db, uuid.UUID(payload.get("sub")))
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    data = create_payload_from_user(db_user)
    token = create_access_token(data=data)
    new_refresh_token = create_refresh_token(data=data)
    return Token(access_token=token, refresh_token=new_refresh_token, token_type="bearer")


@router.get("/me", response_model=TokenData)
def get_me(current_user: TokenData = Depends(get_current_user)):
    """Get current user info"""
    return current_user
