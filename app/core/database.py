import atexit
import os
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

db_fd, db_path = None, None
if settings.ENVIRONMENT == "dev":
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    print("Created database at {}".format(db_path))
    engine = create_engine(f"sqlite:///{db_path}", pool_pre_ping=True)
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=settings.DEBUG,
        pool_size=4,
        max_overflow=6,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def cleanup_dev_db():
    """Clean up dev database on shutdown."""
    if settings.ENVIRONMENT == "dev" and db_path:
        try:
            engine.dispose()
            if db_fd is not None:
                os.close(db_fd)
            os.unlink(db_path)
        except (OSError, PermissionError):
            pass


if settings.ENVIRONMENT == "dev" and settings.TEMPORARY_DB:
    atexit.register(cleanup_dev_db)
