from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.api.dependencies import get_current_user, get_oauth, oauth2_scheme, rate_limit
from app.api.v1.endpoints.user import get_user_service
from app.core.config import settings
from app.core.database import get_db
from app.core.middleware import get_client_ip
from app.core.types import TokenData
from app.domains import UserService
from app.domains.auth.auth_service import AuthService
from app.literals.auth import OAuthProvider
from app.literals.users import OnboardingStep
from app.models import User
from app.schemas import LoginRequest, Token, UserRegister
from app.schemas.auth import (
    MessageResponse,
    PasswordChangeRequest,
    PasswordForgotRequest,
    PasswordResetRequest,
    VerificationConfirmRequest,
    VerificationSendRequest,
)

router = APIRouter()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to inject AuthService."""
    return AuthService(db)


@router.post("/login", response_model=Token)
@rate_limit(max_requests=10, window_seconds=60, per_user=False)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    """
    OAuth2 compatible token endpoint.
    Form data expects 'username' and 'password' fields.
    """
    login_request = LoginRequest(username=form_data.username, password=form_data.password)
    return await service.authenticate_user(login_request)


@router.post("/refresh", response_model=Token)
async def refresh(
    refresh_token: str = Body(..., embed=True),
    service: AuthService = Depends(get_auth_service),
):
    return await service.refresh_token(refresh_token)


@router.get("/me", response_model=TokenData)
def get_me(current_user: TokenData = Depends(get_current_user)):
    """Get current user info"""
    return current_user


@router.get("/logout", status_code=status.HTTP_205_RESET_CONTENT)
async def logout(auth_service: AuthService = Depends(get_auth_service), token: str = Depends(oauth2_scheme)):
    await auth_service.invalidate_token(token)


@router.get("/logout_all", status_code=status.HTTP_205_RESET_CONTENT)
async def logout_all(auth_service: AuthService = Depends(get_auth_service), token: str = Depends(oauth2_scheme)):
    await auth_service.invalidate_tokens(token)


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
# rate_limit here may be unnecessary, because it is already limited in main.py,
# but maybe this is better approach, I dunno
# @rate_limit(max_requests=5, window_seconds=3600, per_user=False)
async def signup(
    request: Request,
    data: UserRegister,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Register a new user, send verification email and auto-login.
    """
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "Unknown")

    user_service.register(data=data, ip_address=client_ip, user_agent=user_agent)
    await auth_service.send_verification_email(data.email)
    login_req = LoginRequest(username=data.email, password=data.password)
    token = await auth_service.authenticate_user(login_req)

    return token


@router.post("/verify/send", response_model=MessageResponse)
@rate_limit(
    max_requests=3,
    window_seconds=settings.VERIFICATION_SEND_COOLDOWN_SECONDS,
    per_user=False,
    key_prefix="verify_email",
)
async def send_verification_email(
    request: Request,
    data: VerificationSendRequest,
    service: AuthService = Depends(get_auth_service),
):
    """
    Send a verification email to the user.
    """
    await service.send_verification_email(data.email)
    return MessageResponse(message="If an account exists with this email, a verification link has been sent.")


@router.post("/verify/confirm", response_model=MessageResponse)
@rate_limit(max_requests=10, window_seconds=60, per_user=False)
async def confirm_email_verification(
    request: Request,
    data: VerificationConfirmRequest,
    service: AuthService = Depends(get_auth_service),
):
    """
    Confirm email verification using the token sent via email.
    """
    await service.confirm_email_verification(data.token)
    return MessageResponse(message="Email verified successfully.")


@router.post("/password/forgot", response_model=MessageResponse)
@rate_limit(
    key_prefix="password_reset",
    max_requests=settings.PASSWORD_RESET_RATE_LIMIT_REQUESTS,
    window_seconds=settings.PASSWORD_RESET_RATE_LIMIT_WINDOW,
)
async def forgot_password(
    request: Request,
    data: PasswordForgotRequest,
    service: AuthService = Depends(get_auth_service),
):
    """
    Request a password reset email.
    """
    client_ip = get_client_ip(request)
    await service.send_password_reset(data.email, client_ip)
    return MessageResponse(message="If an account exists with this email, a password reset link has been sent.")


@router.post("/password/reset", response_model=MessageResponse)
@rate_limit(max_requests=10, window_seconds=3600, per_user=False)
async def reset_password(
    request: Request,
    data: PasswordResetRequest,
    service: AuthService = Depends(get_auth_service),
):
    """
    Reset password using a valid reset token.

    Password requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - Cannot reuse last 5 passwords
    """
    await service.reset_password(data.token, data.new_password)
    return MessageResponse(message="Password reset successfully. Please log in with your new password.")


@router.post("/password/change", response_model=MessageResponse)
async def change_password(
    data: PasswordChangeRequest,
    current_user: TokenData = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """
    Change password for the authenticated user.
    """
    await service.change_password(
        user_id=current_user.id,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    return MessageResponse(message="Password changed successfully.")


####################################################
# Those two should be the last methods on the file #
####################################################


@router.patch("/onboarding/step")
async def update_onboarding_step(
    step: OnboardingStep,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user's current onboarding step."""
    user = db.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.onboarding_step = step.value
    db.commit()
    return {"onboarding_step": step}


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
