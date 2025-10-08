"""Mock data for users and announcements - to be replaced by DB calls in the future."""

import uuid
from typing import Any, Dict, List

from app.core.security import hash_password
from app.models import UserInDB

MOCK_USERS: List[Dict[str, Any]] = [
    {
        "id": uuid.UUID("32ac1969-9800-4ed7-815d-968f5094039e"),
        "username": "aniol0012",
        "email": "aniol0012@gmail.com",
        "first_name": "Aniol",
        "last_name": "Serrano",
        "provider": "local",
        "role": "Basic",
        "phone": "+34612345678",
        "university": "Universitat Politècnica de Catalunya",
    },
    {
        "id": uuid.UUID("0bfeba8c-8e01-49fa-a50a-854ebcd19d41"),
        "username": "admin",
        "email": "admin@admin.com",
        "first_name": "Admin",
        "last_name": "User",
        "provider": "local",
        "role": "Admin",
        "phone": None,
        "university": None,
    },
]

MOCK_ANNOUNCEMENTS: List[Dict[str, Any]] = [
    {
        "id": uuid.uuid4(),
        "title": "Maintenance Notice - Building A",
        "content": "Scheduled maintenance will occur in Building A from 9 AM to 12 PM on Saturday. Please plan "
        "accordingly.",
        "priority": "high",
        "created_by": 1,  # User ID
        "target_rooms": ["A101", "A102", "A103", "A201", "A202"],
        "is_active": True,
        "created_at": "2024-03-01T08:00:00Z",
        "expires_at": "2024-03-15T23:59:59Z",
    },
    {
        "id": uuid.uuid4(),
        "title": "New WiFi Network Available",
        "content": "A new high-speed WiFi network 'UniRoom-5G' is now available in all dormitories. Contact IT for "
        "access credentials.",
        "priority": "medium",
        "created_by": 2,
        "target_rooms": [],  # Empty means all rooms
        "is_active": True,
        "created_at": "2024-03-02T12:00:00Z",
        "expires_at": "2024-04-01T23:59:59Z",
    },
    {
        "id": uuid.uuid4(),
        "title": "Quiet Hours Reminder",
        "content": "Please remember that quiet hours are from 10 PM to 8 AM. Be considerate of your fellow residents.",
        "priority": "low",
        "created_by": 1,
        "target_rooms": [],
        "is_active": True,
        "created_at": "2024-03-03T18:00:00Z",
        "expires_at": "2024-06-01T23:59:59Z",
    },
    {
        "id": uuid.uuid4(),
        "title": "Laundry Room Updates",
        "content": "New washing machines have been installed in Building C. Old machines are out of service.",
        "priority": "medium",
        "created_by": 3,
        "target_rooms": ["C301", "C302", "C303", "C401", "C402"],
        "is_active": True,
        "created_at": "2024-03-04T14:30:00Z",
        "expires_at": "2024-03-20T23:59:59Z",
    },
    {
        "id": uuid.uuid4(),
        "title": "Fire Drill Scheduled",
        "content": "A fire drill will be conducted next Tuesday at 2 PM. Please evacuate promptly when the alarm "
        "sounds.",
        "priority": "high",
        "created_by": 2,
        "target_rooms": [],
        "is_active": False,  # Past announcement
        "created_at": "2024-02-25T10:00:00Z",
        "expires_at": "2024-03-01T23:59:59Z",
    },
]

MOCK_USERS_AUTH: dict[str, UserInDB] = {}


def seed_mock_users(default_password: str = "password123") -> None:
    for u in MOCK_USERS:
        email = u["email"]
        if email not in MOCK_USERS_AUTH:
            MOCK_USERS_AUTH[email] = UserInDB(
                id=str(u["id"]),
                email=email,
                name=u["name"],
                provider="local",
                role="Basic",
                hashed_password=hash_password(default_password),
            )


def get_user_by_id(user_id: uuid.UUID) -> Dict[str, Any] | None:
    """Get a user by ID from mock data."""
    for user in MOCK_USERS:
        if user["id"] == user_id:
            return user
    return None


def get_users_by_room(room_number: str) -> List[Dict[str, Any]]:
    """Get users by room number from mock data."""
    return [user for user in MOCK_USERS if user["room_number"] == room_number]


def get_active_users() -> List[Dict[str, Any]]:
    """Get all active users from mock data."""
    return [user for user in MOCK_USERS if user["is_active"]]


def get_announcement_by_id(announcement_id: int) -> Dict[str, Any] | None:
    """Get an announcement by ID from mock data."""
    for announcement in MOCK_ANNOUNCEMENTS:
        if announcement["id"] == announcement_id:
            return announcement
    return None


def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements from mock data."""
    return [announcement for announcement in MOCK_ANNOUNCEMENTS if announcement["is_active"]]


def get_announcements_for_room(room_number: str) -> List[Dict[str, Any]]:
    """Get announcements that target a specific room or all rooms."""
    return [
        announcement
        for announcement in MOCK_ANNOUNCEMENTS
        if announcement["is_active"]
        and (
            not announcement["target_rooms"]  # Targets all rooms
            or room_number in announcement["target_rooms"]
        )
    ]


def get_announcements_by_priority(priority: str) -> List[Dict[str, Any]]:
    """Get active announcements by priority level."""
    return [
        announcement
        for announcement in MOCK_ANNOUNCEMENTS
        if announcement["is_active"] and announcement["priority"] == priority
    ]
