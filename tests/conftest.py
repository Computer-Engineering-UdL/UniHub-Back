import datetime
import os
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.auth import router as auth_router
from app.core.database import Base, get_db
from app.core.seed import DEFAULT_PASSWORD


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
                else:
                    pass


def seed_database_test(db):
    """Seed test database with initial data."""
    import uuid

    from app.core import hash_password
    from app.models import User

    admin_user = User(
        id=uuid.uuid4(),
        username="admin",
        email="admin@admin.com",
        password=hash_password(DEFAULT_PASSWORD),
        first_name="Admin",
        last_name="User",
        provider="local",
        role="Admin",
        is_active=True,
        is_verified=True,
        created_at=datetime.datetime.now(datetime.UTC),
    )

    test_user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="aniol0012@gmail.com",
        password=hash_password(DEFAULT_PASSWORD),
        first_name="Test",
        last_name="User",
        provider="local",
        role="Basic",
        is_active=True,
        is_verified=True,
        created_at=datetime.datetime.now(datetime.UTC),
    )

    db.add_all([admin_user, test_user])
    db.commit()


@pytest.fixture
def app(db):
    """Create FastAPI app with test database."""
    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db  # type: ignore
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)
