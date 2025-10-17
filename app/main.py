from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models
from app.api.v1.endpoints import (
    auth,
    channel,
    housing_category,
    housing_offer,
    housing_photo,
    interest,
    message,
    user,
)
from app.core.config import settings
from app.core.database import Base, engine
from app.core.seed import seed_database
from app.core.seed_offers import seed_housing_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    seed_database()
    seed_housing_data()
    Base.metadata.create_all(bind=engine)
    print("Tables created, app starting...")
    yield
    # Shutdown logic
    print("App shutting down...")


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

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
# app.include_router(announcement.router, prefix=f"{settings.API_VERSION}/announcements", tags=["announcements"])


@app.get("/")
def read_root():
    """
    Root endpoint for the application.
    """
    return {"message": "Welcome to the UniRoom API!"}