from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Body, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.api.v1.endpoints.user import get_user_service
from app.core import create_access_token
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_oauth
from app.core.security import create_refresh_token
from app.core.types import TokenData
from app.domains import UserService
from app.domains.auth.auth_service import AuthService
from app.literals.auth import OAuthProvider
from app.models import create_payload_from_user
from app.schemas import LoginRequest, Token, UserRegister

router = APIRouter()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to inject AuthService."""
    return AuthService(db)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    """
    OAuth2 compatible token endpoint.
    Form data expects 'username' and 'password' fields.
    """
    login_request = LoginRequest(username=form_data.username, password=form_data.password)
    return service.authenticate_user(login_request)


@router.post("/refresh", response_model=Token)
async def refresh(
    refresh_token: str = Body(..., embed=True),
    service: AuthService = Depends(get_auth_service),
):
    return service.refresh_token(refresh_token)


@router.get("/me", response_model=TokenData)
def get_me(current_user: TokenData = Depends(get_current_user)):
    """Get current user info"""
    return current_user


@router.get("/{provider}", response_class=RedirectResponse, include_in_schema=True)
async def login_oauth(
    provider: OAuthProvider,
    request: Request,
    oauth: OAuth = Depends(get_oauth),
):
    provider_str = provider.value
    redirect_uri = request.url_for("auth_callback", provider=provider_str)
    return await oauth.create_client(provider_str).authorize_redirect(request, redirect_uri)


@router.get("/{provider}/callback", response_model=Token)
async def auth_callback(
    provider: OAuthProvider,
    request: Request,
    service: AuthService = Depends(get_auth_service),
    oauth: OAuth = Depends(get_oauth),
):
    return await service.oauth_callback(provider, request, oauth)

@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(
    data: UserRegister,
    user_service: UserService = Depends(get_user_service),
):
    # Create user (returns UserRead)
    user = user_service.register(data)

    # Fetch ORM instance to build correct JWT payload
    user_orm = user_service.repository.get_by_id(user.id)

    payload = create_payload_from_user(user_orm)

    return Token(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
        token_type="bearer",
    )
