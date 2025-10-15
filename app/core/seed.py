import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core import hash_password
from app.core.database import Base, engine
from app.models import User

DEFAULT_PASSWORD = "unirromsuperadminsecretpassword"


def seed_database():
    """Populate database with initial data on first run."""
    Base.metadata.create_all(bind=engine)

    db = Session(engine)

    try:
        admin = db.query(User).filter_by(email="admin@admin.com").first()
        if admin:
            print("Database already seeded. Skipping...")
            return

        admin_user = User(
            id=uuid.uuid4(),
            username="admin",
            email="admin@admin.com",
            password=hash_password(DEFAULT_PASSWORD),
            first_name="Admin",
            last_name="User",
            phone="+34 666 777 888",
            university="Tech University",
            avatar_url="https://api.example.com/avatars/admin.jpg",
            room_number="101",
            provider="local",
            role="Admin",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
        )

        test_user1 = User(
            id=uuid.uuid4(),
            username="john_doe",
            email="john@example.com",
            password=hash_password(DEFAULT_PASSWORD),
            first_name="John",
            last_name="Doe",
            phone="+34 666 111 222",
            university="Madrid University",
            avatar_url=None,
            room_number="202",
            provider="local",
            role="Basic",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
        )

        test_user2 = User(
            id=uuid.uuid4(),
            username="jane_smith",
            email="jane@example.com",
            password=hash_password(DEFAULT_PASSWORD),
            first_name="Jane",
            last_name="Smith",
            phone="+34 666 333 444",
            university="Barcelona University",
            avatar_url=None,
            room_number="303",
            provider="local",
            role="Basic",
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow(),
        )

        db.add_all([admin_user, test_user1, test_user2])
        db.commit()
        print("Database seeded successfully!")
        print(f"   - Admin: {admin_user.email} / {DEFAULT_PASSWORD}")
        print(f"   - User 1: {test_user1.email} / {DEFAULT_PASSWORD}")
        print(f"   - User 2: {test_user2.email} / {DEFAULT_PASSWORD}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()
