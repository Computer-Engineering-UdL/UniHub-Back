from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Channel, ChannelTableModel, Message


class ChannelCRUD:
    @staticmethod
    def create(db: Session, channel: Channel) -> Channel:
        db_channel = ChannelTableModel(
            name=channel.name,
            description=channel.description,
            channel_type=channel.channel_type,
            channel_logo=str(channel.channel_logo) if channel.channel_logo else None,
        )

        try:
            db.add(db_channel)
            db.commit()
            db.refresh(db_channel)
            return Channel.model_validate(db_channel, from_attributes=True)
        except IntegrityError as e:
            db.rollback()
            raise e

    @staticmethod
    def get_by_id(db: Session, channel_id: str) -> Optional[Channel]:
        try:
            return Channel.model_validate(db.query(ChannelTableModel).get(channel_id), from_attributes=True)
        except ValueError:
            return None

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filter_channel: Optional[str] = None,
    ) -> list[Channel]:
        query = db.query(ChannelTableModel)

        if filter_channel is not None:
            query = query.filter(ChannelTableModel.channel_type.has(channel_type=filter_channel))

        return [
            Channel.model_validate(channel, from_attributes=True) for channel in query.offset(skip).limit(limit).all()
        ]

    @staticmethod
    def get_messages(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        channel_id: Optional[str] = None,
    ) -> list[Message]:
        query = db.query(ChannelTableModel)

        if channel_id is not None:
            query = query.filter(ChannelTableModel.id.has(channel_id=channel_id))

        return [Message.model_validate(msg, from_attributes=True) for msg in query.offset(skip).limit(limit).all()]
