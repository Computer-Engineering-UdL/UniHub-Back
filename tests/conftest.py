import os
import random
import string
import tempfile
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core import Base, get_db
from app.core.config import settings
from app.core.valkey import valkey_client
from app.models import User
from app.schemas import LoginRequest
from app.seeds import seed_channels, seed_housing_data, seed_interests, seed_reports, seed_users
from app.seeds.category import seed_housing_categories
from app.seeds.item_category import seed_item_categories
from app.seeds.messages import seed_messages
from app.seeds.terms import seed_terms

try:
    from app.seeds import seed_universities
except ImportError:
    try:
        from app.seeds.university import seed_universities
    except ImportError:
        seed_universities = None


def seed_database_test(db: Session):
    """Seed test database with initial data."""

    if seed_universities:
        seed_universities(db)

    seed_terms(db)
    users = seed_users(db)
    channels = seed_channels(db, users)
    seed_messages(db, users, channels)
    seed_reports(db, users)
    seed_housing_categories(db)
    seed_housing_data(db, users)
    seed_interests(db)
    seed_item_categories(db)


@pytest.fixture(scope="session")
def engine():
    """Create a SQLite engine for the test session and seed database once."""
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

        # Seed database ONCE per test session
        db_session = Session(bind=_engine)
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
def db(request, engine):
    """
    Provide a SQLAlchemy session per test with full isolation.

    Features:
    - Starts a transaction and nested SAVEPOINT for rollback.
    - By default, uses the session-level seeded database.
    - If the test is marked with @pytest.mark.no_seed:
        - optionally clean relevant tables for a fresh empty DB.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # Nested transaction for test isolation
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    # Check marker to skip seed (i.e., empty DB for this test)
    if request.node.get_closest_marker("no_seed"):
        # nested rollback is enough since seed is session-level
        for table in reversed(Base.metadata.sorted_tables):
            try:
                session.execute(table.delete())
            except Exception:
                pass
        session.commit()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def auth_service(db):
    """Create AuthService instance for tests."""
    from app.domains.auth.auth_service import AuthService

    return AuthService(db)


@pytest.fixture
def user_service(db):
    """Create UserService instance for tests."""
    from app.domains.user.user_service import UserService

    return UserService(db)


@pytest.fixture
def file_service(db):
    """Create FileService instance for tests."""
    from app.domains.file.file_service import FileService

    return FileService(db)


@pytest.fixture
def file_association_service(db):
    """Create FileAssociationService instance for tests."""
    from app.domains.file.file_association_service import FileAssociationService

    return FileAssociationService(db)


@pytest.fixture
def university_service(db):
    """Create UniversityService instance for tests."""
    from app.domains.university.university_service import UniversityService

    return UniversityService(db)


@pytest.fixture
def category_service(db):
    """Create CategoryService instance for tests."""
    from app.domains.housing.category_service import HousingCategoryService

    return HousingCategoryService(db)


@pytest.fixture
def user_repository(db):
    """Create UserRepository instance for tests."""
    from app.domains.user.user_repository import UserRepository

    return UserRepository(db)


@pytest.fixture
def file_repository(db):
    """Create FileRepository instance for tests."""
    from app.domains.file.file_repository import FileRepository

    return FileRepository(db)


@pytest.fixture
def file_association_repository(db):
    """Create FileAssociationRepository instance for tests."""
    from app.domains.file.file_association_repository import FileAssociationRepository

    return FileAssociationRepository(db)


@pytest.fixture
def channel_repository(db):
    """Create ChannelRepository instance for tests."""
    from app.domains.channel.channel_repository import ChannelRepository

    return ChannelRepository(db)


@pytest.fixture
def message_repository(db):
    """Create MessageRepository instance for tests."""
    from app.domains.channel.message_repository import MessageRepository

    return MessageRepository(db)


@pytest.fixture
def conversation_repository(db):
    """Create ConversationRepository instance for tests."""
    from app.domains.housing.conversation_repository import ConversationRepository

    return ConversationRepository(db)


@pytest.fixture
def housing_offer_repository(db):
    """Create HousingOfferRepository instance for tests."""
    from app.domains.housing.offer_repository import HousingOfferRepository

    return HousingOfferRepository(db)


@pytest.fixture
def housing_amenity_repository(db):
    """Create HousingAmenityRepository instance for tests."""
    from app.domains.housing.amenity_repository import HousingAmenityRepository

    return HousingAmenityRepository(db)


@pytest.fixture
def housing_category_repository(db):
    """Create HousingCategoryRepository instance for tests."""
    from app.domains.housing.category_repository import HousingCategoryRepository

    return HousingCategoryRepository(db)


@pytest.fixture
def interest_repository(db):
    """Create InterestRepository instance for tests."""
    from app.domains.user.interest_repository import InterestRepository

    return InterestRepository(db)


@pytest.fixture
def user_like_repository(db):
    """Create UserLikeRepository instance for tests."""
    from app.domains.user.like_repository import UserLikeRepository

    return UserLikeRepository(db)


@pytest.fixture
def university_repository(db):
    """Create UniversityRepository instance for tests."""
    from app.domains.university.university_repository import UniversityRepository

    return UniversityRepository(db)


@pytest.fixture
async def auth_headers(client, db, auth_service):
    """Generate authentication headers for basic_user."""
    user = db.query(User).filter_by(username="basic_user").first()
    token = await auth_service.authenticate_user(
        LoginRequest(username=user.username, password=settings.DEFAULT_PASSWORD)
    )
    return {"Authorization": f"Bearer {token.access_token}"}


@pytest.fixture
def admin_auth_headers(admin_token):
    """Return authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def app(db):
    """Create FastAPI app with test database.

    Router imports are done here (lazy loading) to speed up pytest startup.
    This defers loading the entire application until tests actually need the client.
    """
    from app.api.health import router as health_router
    from app.api.v1.endpoints.admin_reports import router as admin_reports_router
    from app.api.v1.endpoints.auth import router as auth_router
    from app.api.v1.endpoints.channel import router as channel_router
    from app.api.v1.endpoints.connection import router as connection_router
    from app.api.v1.endpoints.conversation import router as conversation_router
    from app.api.v1.endpoints.dashboard import router as dashboard_router
    from app.api.v1.endpoints.file_association import router as file_association_router
    from app.api.v1.endpoints.files import router as file_router
    from app.api.v1.endpoints.housing_category import router as category_router
    from app.api.v1.endpoints.housing_offer import router as housing_offer_router
    from app.api.v1.endpoints.interest import router as interest_router
    from app.api.v1.endpoints.item import router as item_router
    from app.api.v1.endpoints.item_category import router as item_cat_router
    from app.api.v1.endpoints.job_offer import router as job_offer_router
    from app.api.v1.endpoints.members import router as members_router
    from app.api.v1.endpoints.messages import router as messages_router
    from app.api.v1.endpoints.reports import router as reports_router
    from app.api.v1.endpoints.terms import router as terms_router
    from app.api.v1.endpoints.user import router as user_router
    from app.api.v1.endpoints.user_like import router as user_like_router
    from app.api.v1.endpoints.user_terms import router as user_terms_router
    from app.api.v1.endpoints.websocket import router as websocket_router

    app = FastAPI()
    app.include_router(user_router, prefix="/users")
    app.include_router(auth_router, prefix="/auth")
    app.include_router(interest_router, prefix="/interest")
    app.include_router(housing_offer_router, prefix="/offers")
    app.include_router(conversation_router, prefix="/conversations")
    app.include_router(user_like_router, prefix="/user-likes")
    app.include_router(file_router, prefix="/files")
    app.include_router(file_association_router, prefix="/file-associations")
    app.include_router(websocket_router)
    app.include_router(category_router, prefix="/categories")
    app.include_router(dashboard_router, prefix="/dashboard")
    app.include_router(item_router, prefix="/items")
    app.include_router(item_cat_router, prefix="/item-categories")
    app.include_router(job_offer_router, prefix="/jobs")
    app.include_router(terms_router, prefix="/terms")
    app.include_router(user_terms_router, prefix="/user_terms")
    app.include_router(connection_router, prefix="/connection")
    app.include_router(reports_router, prefix="/reports")
    app.include_router(admin_reports_router, prefix="/admin/reports")
    app.include_router(health_router)
    for router in (channel_router, members_router, messages_router):
        app.include_router(router, prefix="/channels")

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    from starlette.middleware.sessions import SessionMiddleware

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        session_cookie="session",
        max_age=3600,
        same_site="lax",
        https_only=False,
    )

    return app


@pytest.fixture(scope="function")
def client(app):
    """
    Create test client with context manager.
    Using the context manager ensures startup/shutdown events are triggered.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function", autouse=True)
async def setup_valkey():
    """
    Initialize Valkey client for tests using fake Redis.
    Scope is function to ensure a fresh client per test and correct loop binding.
    """
    valkey_client._use_fake = True
    valkey_client._client = None

    await valkey_client.connect()

    yield

    await valkey_client.disconnect()


@pytest.fixture
def get_token(client):
    def _get_token(username):
        response = client.post(
            "/auth/login",
            data={"username": username, "password": settings.DEFAULT_PASSWORD},
        )
        return response.json()["access_token"]

    return _get_token


@pytest.fixture
def admin_token(get_token):
    return get_token("admin")


@pytest.fixture
def seller_token(get_token):
    return get_token("jane_smith")


@pytest.fixture
def user_token(get_token):
    return get_token("basic_user")


@pytest.fixture
def user2_token(get_token):
    return get_token("jane_smith")


@pytest.fixture(scope="session", autouse=True)
def configure_test_settings():
    """Configure settings for test environment."""
    if "text/plain" not in settings.ALLOWED_FILE_TYPES:
        settings.ALLOWED_FILE_TYPES = list(settings.ALLOWED_FILE_TYPES) + ["text/plain"]

    settings.TESTING = True

    yield

    settings.TESTING = False


@pytest.fixture
def recruiter_token(client, db):
    """Create user Recruiter global and return her token."""
    import uuid

    from app.core.security import hash_password
    from app.literals.users import Role
    from app.models import User

    def gen_referral():
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=5))

    unique_username = f"recruiter_global_{uuid.uuid4()}"
    user = User(
        username=unique_username,
        email=f"{unique_username}@example.com",
        password=hash_password(settings.DEFAULT_PASSWORD),
        first_name="Recruiter",
        last_name="Global",
        role=Role.RECRUITER,
        provider="local",
        is_verified=True,
        referral_code=gen_referral(),
    )
    db.add(user)
    db.commit()
    response = client.post(
        "/auth/login",
        data={"username": unique_username, "password": settings.DEFAULT_PASSWORD},
    )
    return response.json()["access_token"]
