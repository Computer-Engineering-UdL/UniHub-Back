import datetime
import uuid
from typing import List

from sqlalchemy.orm import Session

from app.core import hash_password
from app.core.config import settings
from app.literals.users import Role
from app.models import User


def seed_users(db: Session) -> List[User]:
    """Create default users and return them."""

    admin = db.query(User).filter_by(email="admin@admin.com").first()
    if admin is not None:
        existing_users = db.query(User).limit(3).all()
        return existing_users

    def make_user(**kwargs) -> User:
        return User(
            id=uuid.uuid4(),
            password=hash_password(settings.DEFAULT_PASSWORD),
            created_at=datetime.datetime.now(datetime.UTC),
            **kwargs,
        )

    users = [
        make_user(
            username="admin",
            email="admin@admin.com",
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
        ),
        make_user(
            username="basic_user",
            email="user@user.com",
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
        ),
        make_user(
            username="jane_smith",
            email="jane@example.com",
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
        ),
        make_user(
            username="carlos_mendez",
            email="carlos.mendez@udl.com",
            first_name="Carlos",
            last_name="Méndez",
            phone="+34 666 555 666",
            university="Universitat Autònoma de Barcelona",
            avatar_url="https://avatar.iran.liara.run/public/56",
            room_number="404",
            provider="local",
            role=Role.BASIC,
            is_active=True,
            is_verified=True,
        ),
        make_user(
            username="lucia_rodriguez",
            email="lucia.rodriguez@ub.edu",
            first_name="Lucía",
            last_name="Rodríguez",
            phone="+34 666 777 999",
            university="Universitat de Barcelona",
            avatar_url="https://avatar.iran.liara.run/public/67",
            room_number="505",
            provider="local",
            role=Role.SELLER,
            is_active=True,
            is_verified=True,
        ),
        make_user(
            username="marc_torres",
            email="marc.torres@urv.cat",
            first_name="Marc",
            last_name="Torres",
            phone="+34 666 888 000",
            university="Universitat Rovira i Virgili",
            avatar_url="https://avatar.iran.liara.run/public/78",
            room_number="606",
            provider="local",
            role=Role.BASIC,
            is_active=True,
            is_verified=False,
        ),
        make_user(
            username="sofia_martinez",
            email="sofia.martinez@uab.es",
            first_name="Sofía",
            last_name="Martínez",
            phone="+34 666 123 456",
            university="Universitat Autònoma de Barcelona",
            avatar_url="https://avatar.iran.liara.run/public/89",
            room_number="707",
            provider="google",
            role=Role.BASIC,
            is_active=True,
            is_verified=True,
        ),
        make_user(
            username="andreu_vila",
            email="andreu.vila@udg.cat",
            first_name="Andreu",
            last_name="Vila",
            phone="+34 666 234 567",
            university="Universitat de Girona",
            avatar_url="https://avatar.iran.liara.run/public/91",
            room_number="808",
            provider="local",
            role=Role.SELLER,
            is_active=False,
            is_verified=False,
        ),
        make_user(
            username="paula_hernandez",
            email="paula.hernandez@upc.edu",
            first_name="Paula",
            last_name="Hernández",
            phone="+34 666 345 678",
            university="Universitat Politècnica de Catalunya",
            avatar_url="https://avatar.iran.liara.run/public/101",
            room_number="909",
            provider="local",
            role=Role.ADMIN,
            is_active=True,
            is_verified=True,
        ),
        make_user(
            username="david_pons",
            email="david.pons@udl.com",
            first_name="David",
            last_name="Pons",
            phone="+34 666 987 654",
            university="Universitat de Lleida",
            avatar_url="https://avatar.iran.liara.run/public/112",
            room_number="111",
            provider="google",
            role=Role.BASIC,
            is_active=True,
            is_verified=True,
        ),
        make_user(
            username="elena_costa",
            email="elena.costa@urv.cat",
            first_name="Elena",
            last_name="Costa",
            phone="+34 666 765 432",
            university="Universitat Rovira i Virgili",
            avatar_url="https://avatar.iran.liara.run/public/120",
            room_number="212",
            provider="local",
            role=Role.SELLER,
            is_active=True,
            is_verified=True,
        ),
    ]

    db.add_all(users)
    db.flush()

    print("* Users created:")
    print(f"- Admin: {users[0].email} / {settings.DEFAULT_PASSWORD}")
    print(f"- User 1: {users[1].email} / {settings.DEFAULT_PASSWORD}")
    print(f"- User 2: {users[2].email} / {settings.DEFAULT_PASSWORD}")
    print(f"> Total users added: {len(users)}")

    return users
