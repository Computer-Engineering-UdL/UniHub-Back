from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models
from app.api.v1.endpoints import announcement, auth, channel, message, user
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
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

app.include_router(message.router, prefix=f"{settings.API_VERSION}/message", tags=["message"])
app.include_router(channel.router, prefix=f"{settings.API_VERSION}/channel", tags=["channel"])
app.include_router(user.router, prefix=f"{settings.API_VERSION}/user", tags=["user"])

app.include_router(announcement.router, prefix=f"{settings.API_VERSION}/announcements", tags=["announcements"])

app.include_router(auth.router, prefix=f"{settings.API_VERSION}/auth", tags=["auth"])


@app.get("/")
def read_root():
    """
    Root endpoint for the application.
    """
    return {"message": "Welcome to the UniRoom API!"}
