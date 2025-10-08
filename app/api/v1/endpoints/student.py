from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.services.mock_data import (
    MOCK_USERS,
    get_active_users,
    get_user_by_id,
    get_users_by_room,
)

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
def fetch_students():
    """
    Retrieve all students.
    """
    return MOCK_USERS


@router.get("/active", response_model=List[Dict[str, Any]])
def fetch_active_students():
    """
    Retrieve only active students.
    """
    return get_active_users()


@router.get("/room/{room_number}", response_model=List[Dict[str, Any]])
def fetch_students_by_room(room_number: str):
    """
    Retrieve students by room number.
    """
    return get_users_by_room(room_number)


@router.get("/{student_id}", response_model=Dict[str, Any])
def fetch_student(student_id: UUID):
    """
    Retrieve a single student by its ID.
    """
    student = get_user_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student
