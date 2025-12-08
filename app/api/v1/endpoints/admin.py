from fastapi import APIRouter, Depends
from starlette import status
from starlette.exceptions import HTTPException

from app.api.dependencies import cooldown, require_role
from app.core.types import TokenData
from app.literals.users import Role
from app.seeds.seed import seed_database

router = APIRouter()


@router.post("/reset-db", status_code=status.HTTP_200_OK)
@cooldown(action="reset_db", cooldown_seconds=30)
def reset_db(
    current_user: TokenData = Depends(require_role(Role.ADMIN)),
):
    """Reset the database to the seeding state."""
    try:
        seed_database(nuke=True)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset database",
        )

    return {"detail": "Database reset successfully"}
