import datetime

from fastapi import APIRouter, Depends
from redis import Redis
from starlette import status
from starlette.exceptions import HTTPException

from app.core.config import settings
from app.core.dependencies import get_redis, require_role
from app.literals.users import Role
from app.models import ChannelMember
from app.seeds.seed import seed_database

router = APIRouter()


@router.post("/reset-db", status_code=status.HTTP_200_OK)
def reset_db(
    redis: Redis = Depends(get_redis),
    _: ChannelMember = Depends(require_role(Role.ADMIN)),
):
    """Reset the database to the seeding state."""
    if redis.exists("nuke_cooldown"):
        next_cooldown = datetime.datetime.fromtimestamp(float(redis.get("nuke_cooldown")), tz=datetime.UTC)
        if next_cooldown > datetime.datetime.now(datetime.UTC):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
            )
    now = datetime.datetime.now(datetime.UTC)
    next_cooldown = now + datetime.timedelta(seconds=settings.NUKE_COOLDOWN_SECONDS)
    redis.setex("nuke_cooldown", settings.NUKE_COOLDOWN_SECONDS, str(next_cooldown.timestamp()))
    try:
        seed_database(nuke=True)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset database",
        )

    return {"detail": "Database reset successfully"}
