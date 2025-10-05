from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import announcement, auth, student
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(student.router, prefix=f"{settings.API_V1_STR}/students", tags=["students"])

app.include_router(announcement.router, prefix=f"{settings.API_V1_STR}/announcements", tags=["announcements"])

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])


@app.get("/")
def read_root():
    """
    Root endpoint for the application.
    """
    return {"message": "Welcome to the UniRoom API!"}
