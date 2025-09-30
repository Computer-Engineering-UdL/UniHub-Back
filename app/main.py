from fastapi import FastAPI
from app.api.v1.endpoints import student
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME)

app.include_router(
    student.router, prefix=f"{settings.API_V1_STR}/students", tags=["students"]
)


@app.get("/")
def read_root():
    """
    Root endpoint for the application.
    """
    return {"message": "Hello World!"}
