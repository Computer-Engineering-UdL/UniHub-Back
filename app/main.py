from contextlib import asynccontextmanager

import fakeredis
import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

import app.models
from app.api.v1.endpoints import (
    admin,
    auth,
    channel,
    housing_category,
    housing_offer,
    housing_photo,
    interest,
    message,
    user,
)
from app.core import Base, engine
from app.core.config import settings
from app.seeds.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Startup logic
        if settings.USE_FAKE_REDIS:
            app.state.redis = fakeredis.FakeRedis(decode_responses=True)
        else:
            app.state.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT_NUMBER,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
            )
        seed_database()
        Base.metadata.create_all(bind=engine)
        print("Tables created, app starting...")
        yield
    finally:
        if not settings.USE_FAKE_REDIS:
            await app.state.redis.close()
        # Shutdown logic
        print("App shutting down...")


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="session",
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=False,  # Set to True in production
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_VERSION}/auth", tags=["auth"])
app.include_router(user.router, prefix=f"{settings.API_VERSION}/user", tags=["user"])
app.include_router(channel.router, prefix=f"{settings.API_VERSION}/channel", tags=["channel"])
app.include_router(message.router, prefix=f"{settings.API_VERSION}/message", tags=["message"])
app.include_router(housing_offer.router, prefix=f"{settings.API_VERSION}/offers", tags=["housing offers"])
app.include_router(housing_category.router, prefix=f"{settings.API_VERSION}/categories", tags=["housing categories"])
app.include_router(housing_photo.router, prefix=f"{settings.API_VERSION}/photos", tags=["housing photos"])
app.include_router(interest.router, prefix=f"{settings.API_VERSION}/interest", tags=["interest"])
app.include_router(admin.router, prefix=f"{settings.API_VERSION}/admin", tags=["admin"])


# app.include_router(announcement.router, prefix=f"{settings.API_VERSION}/announcements", tags=["announcements"])


@app.get("/")
def read_root():
    """
    Root endpoint for the application.
    """
    return {"message": "Welcome to the UniHub API!"}
