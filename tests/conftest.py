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
from app.api.v1.endpoints.user import router as user_router
from app.core import Base, get_db
from app.core.config import settings
from app.models import User
from app.schemas import LoginRequest
from app.seeds import seed_channels, seed_housing_data, seed_interests, seed_users
from app.seeds.messages import seed_messages
from app.services import authenticate_user


@pytest.fixture
def auth_headers(client, db):
    """Generate authentication headers for basic_user."""
    user = db.query(User).filter_by(username="basic_user").first()
    token = authenticate_user(db, LoginRequest(username=user.username, password=settings.DEFAULT_PASSWORD))
    return {"Authorization": f"Bearer {token.access_token}"}


@pytest.fixture(scope="function")
def db():
    """Create a temporary SQLite database for testing."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    try:
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=None,
        )

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
    users = seed_users(db)
    channels = seed_channels(db, users)
    seed_messages(db, users, channels)
    seed_housing_data(db)
    seed_interests(db)


@pytest.fixture
def app(db):
    """Create FastAPI app with test database."""
    app = FastAPI()
    app.include_router(user_router, prefix="/users")
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
    response = client.post(
        "/auth/login",
        data={"username": "basic_user", "password": settings.DEFAULT_PASSWORD},
    )
    return response.json()["access_token"]


@pytest.fixture
def user2_token(client):
    """Get second regular user access token."""
    response = client.post(
        "/auth/login",
        data={"username": "jane_smith", "password": settings.DEFAULT_PASSWORD},
    )
    return response.json()["access_token"]
