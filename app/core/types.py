import uuid

from pydantic import BaseModel

from app.literals.users import OnboardingStep, Role


class TokenData(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: Role = Role.BASIC
    onboarding_step: str = OnboardingStep.NOT_STARTED
