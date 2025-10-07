from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.channel import ChannelCRUD
from app.models import Channel

router = APIRouter()


@router.get("/", response_model=List[Channel])
def fetch_channels(db: Session = Depends(get_db)):
    """
    Retrieve all public channels.
    """
    return ChannelCRUD.get_all(db)


@router.get("/{channel_id}", response_model=Channel)
def fetch_channel(channel_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a specific channel.
    """
    return ChannelCRUD.get_by_id(db, channel_id)


@router.post("/", response_model=Channel)
def create_channel(channel: Channel, db: Session = Depends(get_db)):
    """
    Create a new channel.
    """
    return ChannelCRUD.create(db, channel)
