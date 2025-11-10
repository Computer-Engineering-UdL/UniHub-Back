import uuid
from typing import List

from pydantic import BaseModel, ConfigDict


class UniversitySimpleRead(BaseModel):
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)


class FacultySimpleRead(BaseModel):
    id: uuid.UUID
    name: str
    address: str | None
    model_config = ConfigDict(from_attributes=True)


class FacultyRead(FacultySimpleRead):
    university: UniversitySimpleRead
    model_config = ConfigDict(from_attributes=True)


class UniversityRead(UniversitySimpleRead):
    faculties: List[FacultySimpleRead] = []
    model_config = ConfigDict(from_attributes=True)


__all__ = ["FacultyRead", "UniversityRead", "FacultySimpleRead", "UniversitySimpleRead"]
