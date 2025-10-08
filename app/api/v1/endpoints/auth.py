from fastapi import APIRouter, HTTPException, status

from app.core.security import create_access_token
from app.models import AuthResponse, LoginRequest, UserPublic
from app.services.mock_data import MOCK_USERS

router = APIRouter()

# This will be removed, but for now this is the default password for all mock users
DEFAULT_PASSWORD = "unirromsuperadminsecretpassword"


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    user = next((u for u in MOCK_USERS if u["email"] == payload.email), None)
    if not user or payload.password != DEFAULT_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(sub=str(user["id"]))
    user_public = UserPublic(**user)
    return AuthResponse(token=token, user=user_public)
