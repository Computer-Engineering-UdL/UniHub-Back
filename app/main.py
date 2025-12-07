import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

import app.models
from app.api.v1.endpoints import (
    admin,
    auth,
    channel,
    connection,
    conversation,
    dashboard,
    file_association,
    files,
    housing_amenity,
    housing_category,
    housing_offer,
    interest,
    job_offer,
    members,
    messages,
    terms,
    university,
    user,
    user_like,
    user_terms,
    websocket,
)
from app.core import Base, engine
from app.core.config import settings
from app.core.middleware import AutoLoggingMiddleware, EndpointRateLimitMiddleware, global_exception_handler
from app.core.valkey import valkey_client
from app.seeds.seed import seed_database

uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_error_logger = logging.getLogger("uvicorn.error")

uvicorn_access_logger.propagate = False
uvicorn_error_logger.propagate = False

uvicorn_access_logger.handlers = []
uvicorn_error_logger.handlers = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        seed_database()
        Base.metadata.create_all(bind=engine)
        await valkey_client.connect()
        print("Tables created, app starting...")
        yield
    finally:
        print("App shutting down...")
        await valkey_client.disconnect()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(AutoLoggingMiddleware)

api_prefix = settings.API_VERSION
endpoint_limits = {
    # Signup: 5 tries per 1 hour from one IP address
    f"{api_prefix}/auth/signup": (5, 3600),
}
app.add_middleware(EndpointRateLimitMiddleware, endpoint_limits=endpoint_limits)

app.exception_handler(Exception)(global_exception_handler)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="session",
    max_age=3600,
    same_site="lax",
    https_only=settings.ENVIRONMENT != "dev",
)

if settings.ENVIRONMENT != "dev":
    origins = [
        "https://computer-engineering-udl.github.io",
    ]
else:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_VERSION}/auth", tags=["auth"])
app.include_router(user.router, prefix=f"{settings.API_VERSION}/user", tags=["user"])
app.include_router(channel.router, prefix=f"{settings.API_VERSION}/channel", tags=["channel"])
app.include_router(members.router, prefix=f"{settings.API_VERSION}/channel", tags=["channel members"])
app.include_router(messages.router, prefix=f"{settings.API_VERSION}/channel", tags=["channel messages"])

app.include_router(conversation.router, prefix=f"{settings.API_VERSION}/conversation", tags=["conversation"])

app.include_router(dashboard.router, prefix=f"{settings.API_VERSION}/dashboard", tags=["dashboard"])

app.include_router(
    housing_offer.router,
    prefix=f"{settings.API_VERSION}/offers",
    tags=["housing offers"],
)
app.include_router(
    housing_category.router,
    prefix=f"{settings.API_VERSION}/categories",
    tags=["housing categories"],
)
app.include_router(
    housing_amenity.router,
    prefix=f"{settings.API_VERSION}/amenities",
    tags=["housing amenities"],
)
app.include_router(user_like.router, prefix=f"{settings.API_VERSION}/likes", tags=["user likes"])
app.include_router(interest.router, prefix=f"{settings.API_VERSION}/interest", tags=["interest"])
app.include_router(admin.router, prefix=f"{settings.API_VERSION}/admin", tags=["admin"])
app.include_router(files.router, prefix=f"{settings.API_VERSION}/files", tags=["files"])
app.include_router(
    file_association.router, prefix=f"{settings.API_VERSION}/file-associations", tags=["file associations"]
)
app.include_router(university.router, prefix=f"{settings.API_VERSION}/universities", tags=["universities"])
app.include_router(websocket.router, tags=["websocket"])
app.include_router(terms.router, prefix=f"{settings.API_VERSION}/terms", tags=["terms"])
app.include_router(user_terms.router, prefix=f"{settings.API_VERSION}/user_terms", tags=["user_terms"])
app.include_router(connection.router,prefix=f"{settings.API_VERSION}/connection", tags=["connection"])

@app.get("/")
def read_root():
    """
    Root endpoint for the application.
    """
    return {"message": "Welcome to the UniHub API!"}
