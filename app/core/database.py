from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

if settings.ENVIRONMENT == "dev":
    engine = create_engine("sqlite:///./test.db", pool_pre_ping=True)
else:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=settings.DEBUG, pool_size=4, max_overflow=6)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
