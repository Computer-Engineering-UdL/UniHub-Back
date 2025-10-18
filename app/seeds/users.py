import datetime
import uuid
from typing import List

from sqlalchemy.orm import Session

from app.core import hash_password
from app.core.config import settings
from app.literals.users import Role
from app.models import User


def seed_users(db: Session) -> List[User]:
    """Create default users.

    Returns:
        List of created users [admin, test_user1, test_user2]
    """

    admin = db.query(User).filter_by(email="admin@admin.com").first()
    if admin is not None:
        test_user1 = db.query(User).filter_by(email="john@example.com").first()
        test_user2 = db.query(User).filter_by(email="jane@example.com").first()
        return [admin, test_user1, test_user2]

    admin_user = User(
        id=uuid.uuid4(),
        username="admin",
        email="admin@admin.com",
        password=hash_password(settings.DEFAULT_PASSWORD),
        first_name="Admin",
        last_name="User",
        phone="+34 666 777 888",
        university="Universitat de Lleida",
        avatar_url="https://avatar.iran.liara.run/public/12",
        room_number="101",
        provider="local",
        role=Role.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime.datetime.now(datetime.UTC),
    )

    test_user1 = User(
        id=uuid.uuid4(),
        username="basic_user",
        email="user@user.com",
        password=hash_password(settings.DEFAULT_PASSWORD),
        first_name="Joan",
        last_name="Pere",
        phone="+34 666 111 222",
        university="Universitat de Lleida",
        avatar_url="https://avatar.iran.liara.run/public/34",
        room_number="202",
        provider="local",
        role=Role.BASIC,
        is_active=True,
        is_verified=True,
        created_at=datetime.datetime.now(datetime.UTC),
    )

    test_user2 = User(
        id=uuid.uuid4(),
        username="jane_smith",
        email="jane@example.com",
        password=hash_password(settings.DEFAULT_PASSWORD),
        first_name="Jane",
        last_name="Smith",
        phone="+34 666 333 444",
        university="Universitat de Barcelona",
        avatar_url="https://avatar.iran.liara.run/public/45",
        room_number="303",
        provider="local",
        role=Role.SELLER,
        is_active=True,
        is_verified=True,
        created_at=datetime.datetime.now(datetime.UTC),
    )

    db.add_all([admin_user, test_user1, test_user2])
    db.flush()

    print("* Users created:")
    print(f"- Admin: {admin_user.email} / {settings.DEFAULT_PASSWORD}")
    print(f"- User 1: {test_user1.email} / {settings.DEFAULT_PASSWORD}")
    print(f"- User 2: {test_user2.email} / {settings.DEFAULT_PASSWORD}")

    return [admin_user, test_user1, test_user2]
