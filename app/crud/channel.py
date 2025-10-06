from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.channel import Channel, ChannelTableModel


class ChannelCRUD:
    @staticmethod
    def create(db: Session, channel: Channel) -> ChannelTableModel:
        db_channel = ChannelTableModel(
            id=channel.id,
            name=channel.name,
            description=channel.description,
            channel_type=channel.channel_type,
            channel_logo=str(channel.channel_logo) if channel.channel_logo else None,
        )

        try:
            db.add(db_channel)
            db.commit()
            db.refresh(db_channel)
            return db_channel
        except IntegrityError as e:
            db.rollback()
            raise e

    @staticmethod
    def get_by_id(db: Session, channel_id: str) -> Optional[ChannelTableModel]:
        try:
            return db.query(ChannelTableModel).get(channel_id)
        except ValueError:
            return None

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filter_channel: Optional[str] = None,
    ) -> list[type[ChannelTableModel]]:
        query = db.query(ChannelTableModel)

        if filter_channel is not None:
            query = query.filter(ChannelTableModel.channel_type.has(channel_type=filter_channel))

        return query.offset(skip).limit(limit).all()
