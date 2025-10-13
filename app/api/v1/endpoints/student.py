from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.schemas import UserRead
from app.services.mock_data import (
    MOCK_USERS,
    get_active_users,
    get_user_by_id,
    get_users_by_room,
)

router = APIRouter()


@router.get("/", response_model=List[UserRead])
def fetch_students():
    """
    Retrieve all students.
    """
    return [UserRead(**user.model_dump()) for user in MOCK_USERS]


@router.get("/active", response_model=List[UserRead])
def fetch_active_students():
    """
    Retrieve only active students.
    """
    users = get_active_users()
    return [UserRead(**user.model_dump()) for user in users]


@router.get("/room/{room_number}", response_model=List[UserRead])
def fetch_students_by_room(room_number: str):
    """
    Retrieve students by room number.
    """
    users = get_users_by_room(room_number)
    return [UserRead(**user.model_dump()) for user in users]


@router.get("/{student_id}", response_model=UserRead)
def fetch_student(student_id: UUID):
    """
    Retrieve a single student by its ID.
    """
    student = get_user_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return UserRead(**student.model_dump())
