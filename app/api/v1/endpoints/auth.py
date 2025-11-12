import uuid

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.core import create_access_token
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_oauth
from app.core.security import create_refresh_token
from app.core.types import TokenData
from app.crud.user import UserCRUD
from app.literals.auth import OAuthProvider
from app.models import create_payload_from_user
from app.schemas import LoginRequest, Token
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


@router.get("/{provider}", response_class=RedirectResponse, include_in_schema=True)
async def login_oauth(provider: OAuthProvider, request: Request, oauth: OAuth = Depends(get_oauth)):
    provider_str = provider.value
    redirect_uri = request.url_for("auth_callback", provider=provider_str)
    return await oauth.create_client(provider_str).authorize_redirect(request, redirect_uri)


@router.get("/{provider}/callback", response_model=Token)
async def auth_callback(
    provider: OAuthProvider,
    request: Request,
    db: Session = Depends(get_db),
    oauth: OAuth = Depends(get_oauth),
):
    provider_str = provider.value
    oauth_client = oauth.create_client(provider_str)
    token = await oauth_client.authorize_access_token(request)
    if provider == OAuthProvider.GOOGLE:
        user_info = token.get("userinfo")
        if not user_info:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
        email = user_info["email"]
    elif provider == OAuthProvider.GITHUB:
        email_resp = await oauth_client.get("user/emails", token=token)
        email = next(e["email"] for e in email_resp.json() if e["primary"])
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported OAuth provider")

    try:
        db_user = UserCRUD.get_by_email(db, email)
    except NoResultFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please register first.",
        )

    data = create_payload_from_user(db_user)
    access_token = create_access_token(data=data)
    refresh_token = create_refresh_token(data=data)

    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


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
