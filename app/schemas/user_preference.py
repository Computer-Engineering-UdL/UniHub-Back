import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class UserPreferenceBase(BaseModel):
    email_enabled: bool = True
    push_enabled: bool = True
    in_app_enabled: bool = True
    marketing_opt_in: bool = False

    quiet_hours_start: Optional[datetime.time] = None
    quiet_hours_end: Optional[datetime.time] = None

    @field_validator("quiet_hours_start", "quiet_hours_end", mode="before")
    def parse_time_string(cls, v):
        """Allows passing time as string 'HH:MM'."""
        if isinstance(v, str):
            try:
                return datetime.datetime.strptime(v, "%H:%M").time()
            except ValueError:
                raise ValueError("Time must be in HH:MM format")
        return v


class UserPreferenceCreate(UserPreferenceBase):
    pass


class UserPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    marketing_opt_in: Optional[bool] = None
    quiet_hours_start: Optional[datetime.time] = None
    quiet_hours_end: Optional[datetime.time] = None

    @field_validator("quiet_hours_start", "quiet_hours_end", mode="before")
    def parse_time_string(cls, v):
        if isinstance(v, str):
            return datetime.datetime.strptime(v, "%H:%M").time()
        return v


class UserPreferenceRead(UserPreferenceBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

__all__ = [
    "UserPreferenceBase",
    "UserPreferenceRead",
    "UserPreferenceCreate",
    "UserPreferenceUpdate",
]
