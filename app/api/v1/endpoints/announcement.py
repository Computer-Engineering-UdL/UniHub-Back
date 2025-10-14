from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.services.mock_data import (
    MOCK_ANNOUNCEMENTS,
    get_active_announcements,
    get_announcement_by_id,
    get_announcements_by_priority,
    get_announcements_for_room,
)

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
def fetch_announcements():
    """
    Retrieve all announcements.
    """
    return MOCK_ANNOUNCEMENTS


@router.get("/active", response_model=List[Dict[str, Any]])
def fetch_active_announcements():
    """
    Retrieve only active announcements.
    """
    return get_active_announcements()


@router.get("/room/{room_number}", response_model=List[Dict[str, Any]])
def fetch_announcements_for_room(room_number: str):
    """
    Retrieve announcements that target a specific room or all rooms.
    """
    return get_announcements_for_room(room_number)


@router.get("/priority/{priority}", response_model=List[Dict[str, Any]])
def fetch_announcements_by_priority(priority: str):
    """
    Retrieve active announcements by priority level (low, medium, high).
    """
    valid_priorities = ["low", "medium", "high"]
    if priority not in valid_priorities:
        raise HTTPException(status_code=400, detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}")
    return get_announcements_by_priority(priority)


@router.get("/{announcement_id}", response_model=Dict[str, Any])
def fetch_announcement(announcement_id: int):
    """
    Retrieve a single announcement by its ID.
    """
    announcement = get_announcement_by_id(announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return announcement
