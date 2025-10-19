import datetime
import os
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.channel import router as channel_router
from app.api.v1.endpoints.interest import router as interest_router
from app.core import Base, get_db
from app.core.config import settings
from app.literals.users import Role
from app.seeds import seed_interests


@pytest.fixture(scope="function")
def db():
    """Create a temporary SQLite database for testing."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    try:
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, poolclass=None)

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

        Base.metadata.create_all(bind=engine)

        SessionLocal = sessionmaker(bind=engine)
        db_session = SessionLocal()

        seed_database_test(db_session)
        yield db_session

        db_session.close()
        engine.dispose()

    finally:
        try:
            os.close(db_fd)
        except OSError:
            pass

        for attempt in range(3):
            try:
                os.unlink(db_path)
                break
            except PermissionError:
                if attempt < 2:
                    import time

                    time.sleep(0.1)


def seed_database_test(db):
    """Seed test database with initial data."""
    import uuid

    from app.core import hash_password
    from app.models import User

    admin_user = User(
        id=uuid.uuid4(),
        username="admin",
        email="admin@admin.com",
        password=hash_password(settings.DEFAULT_PASSWORD),
        first_name="Admin",
        last_name="User",
        provider="local",
        role=Role.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime.datetime.now(datetime.UTC),
    )

    test_user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        password=hash_password(settings.DEFAULT_PASSWORD),
        first_name="Test",
        last_name="User",
        provider="local",
        role=Role.BASIC,
        is_active=True,
        is_verified=True,
        created_at=datetime.datetime.now(datetime.UTC),
    )

    test_user2 = User(
        id=uuid.uuid4(),
        username="testuser2",
        email="test2@example.com",
        password=hash_password(settings.DEFAULT_PASSWORD),
        first_name="Test2",
        last_name="User2",
        provider="local",
        role=Role.BASIC,
        is_active=True,
        is_verified=True,
        created_at=datetime.datetime.now(datetime.UTC),
    )

    seed_interests(db)

    db.add_all([admin_user, test_user, test_user2])
    db.commit()


@pytest.fixture
def app(db):
    """Create FastAPI app with test database."""
    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")
    app.include_router(interest_router, prefix="/interest")
    app.include_router(channel_router, prefix="/channels")

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db  # type: ignore
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    """Get admin access token."""
    response = client.post("/auth/login", data={"username": "admin", "password": settings.DEFAULT_PASSWORD})
    return response.json()["access_token"]


@pytest.fixture
def user_token(client):
    """Get regular user access token."""
    response = client.post("/auth/login", data={"username": "testuser", "password": settings.DEFAULT_PASSWORD})
    return response.json()["access_token"]


@pytest.fixture
def user2_token(client):
    """Get second regular user access token."""
    response = client.post("/auth/login", data={"username": "testuser2", "password": settings.DEFAULT_PASSWORD})
    return response.json()["access_token"]
