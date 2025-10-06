from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
def fetch_messages(db: Session = Depends(get_db)):
    """
    Retrieve all messages.
    """
    return {}
