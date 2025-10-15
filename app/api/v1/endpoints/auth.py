from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas import LoginRequest, Token, TokenData
from app.services import authenticate_user

router = APIRouter()


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 compatible token endpoint.
    Form data expects 'username' and 'password' fields.
    """
    login_request = LoginRequest(username=form_data.username, password=form_data.password)

    return authenticate_user(db, login_request)


@router.get("/me", response_model=TokenData)
def get_me(current_user: TokenData = Depends(get_current_user)):
    """Get current user info"""
    return current_user
