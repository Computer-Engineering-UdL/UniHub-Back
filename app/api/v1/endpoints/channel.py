from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
def fetch_channels():
    """
    Retrieve all public channels.
    """
    return {}
