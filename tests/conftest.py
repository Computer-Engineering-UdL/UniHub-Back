import asyncio
import os
import tempfile
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.channel import router as channel_router
from app.api.v1.endpoints.conversation import router as conversation_router
from app.api.v1.endpoints.file_association import router as file_association_router
from app.api.v1.endpoints.files import router as file_router
from app.api.v1.endpoints.housing_offer import router as housing_offer_router
from app.api.v1.endpoints.interest import router as interest_router
from app.api.v1.endpoints.members import router as members_router
from app.api.v1.endpoints.messages import router as messages_router
from app.api.v1.endpoints.user import router as user_router
from app.api.v1.endpoints.user_like import router as user_like_router
from app.core import Base, get_db
from app.core.config import settings
from app.core.valkey import valkey_client
from app.models import User
from app.schemas import LoginRequest
from app.seeds import seed_channels, seed_housing_data, seed_interests, seed_users
from app.seeds.messages import seed_messages
from app.services import authenticate_user


def seed_database_test(db: Session):
    """Seed test database with initial data."""
    users = seed_users(db)
    channels = seed_channels(db, users)
    seed_messages(db, users, channels)
    seed_housing_data(db)
    seed_interests(db)


@pytest.fixture(scope="session")
def engine():
    """Create a temporary SQLite database engine for the entire test session."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    try:
        _engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

        Base.metadata.create_all(bind=_engine)

        SessionLocal = sessionmaker(bind=_engine)
        db_session = SessionLocal()

        seed_database_test(db_session)

        db_session.commit()

        db_session.close()

        yield _engine

        _engine.dispose()

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
                    time.sleep(0.1)


@pytest.fixture(scope="function")
def db(engine):
    """
    Create a new database session for a test, wrapped in a transaction.
    The transaction is rolled back after the test completes.
    """
    connection = engine.connect()
    transaction = connection.begin()
    db_session = Session(bind=connection)

    yield db_session

    transaction.rollback()
    db_session.close()
    connection.close()


@pytest.fixture
def auth_headers(client, db):
    """Generate authentication headers for basic_user."""
    user = db.query(User).filter_by(username="basic_user").first()
    token = authenticate_user(db, LoginRequest(username=user.username, password=settings.DEFAULT_PASSWORD))
    return {"Authorization": f"Bearer {token.access_token}"}


@pytest.fixture
def admin_auth_headers(admin_token):
    """Return authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def app(db):
    """Create FastAPI app with test database."""
    app = FastAPI()
    app.include_router(user_router, prefix="/users")
    app.include_router(auth_router, prefix="/auth")
    app.include_router(interest_router, prefix="/interest")
    app.include_router(channel_router, prefix="/channels")
    app.include_router(members_router, prefix="/channels")
    app.include_router(messages_router, prefix="/channels")
    app.include_router(housing_offer_router, prefix="/offers")
    app.include_router(conversation_router, prefix="/conversations")
    app.include_router(user_like_router, prefix="/user-likes")
    app.include_router(file_router, prefix="/files")
    app.include_router(file_association_router, prefix="/file-associations")

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture(scope="function")
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    """Get admin access token."""
    response = client.post("/auth/login", data={"username": "admin", "password": settings.DEFAULT_PASSWORD})
    return response.json()["access_token"]


@pytest.fixture
def seller_token(client):
    """Get seller user access token."""
    response = client.post(
        "/auth/login",
        data={"username": "jane_smith", "password": settings.DEFAULT_PASSWORD},
    )
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


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_valkey():
    """Initialize Valkey client for tests using fake Redis."""

    valkey_client._is_fake = True
    valkey_client._client = None
    await valkey_client.connect()
    yield
    await valkey_client.disconnect()


@pytest.fixture(autouse=True)
async def clear_valkey():
    """Clear Valkey data between tests to avoid interference."""
    if valkey_client._client:
        try:
            await valkey_client._client.flushdb()
        except Exception:
            pass
    yield


@pytest.fixture(scope="session", autouse=True)
def configure_test_settings():
    """Configure settings for test environment."""

    if "text/plain" not in settings.ALLOWED_FILE_TYPES:
        settings.ALLOWED_FILE_TYPES = list(settings.ALLOWED_FILE_TYPES) + ["text/plain"]

    settings.TESTING = True

    yield

    settings.TESTING = False
