from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.channel import ChannelCRUD

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
def fetch_channels(db: Session = Depends(get_db)):
    """
    Retrieve all public channels.
    """
    return ChannelCRUD.get_all(db)
