from datetime import datetime
from typing import List

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from app.models import User
from app.models.channel import Channel
from app.models.housing_offer import HousingOfferTableModel
from app.models.message import Message


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_users(self) -> int:
        stmt = select(func.count(User.id))
        return self.db.scalar(stmt) or 0

    def count_verified_users(self) -> int:
        stmt = select(func.count(User.id)).where(User.is_verified.is_(True))
        return self.db.scalar(stmt) or 0

    def count_users_created_after(self, date_limit: datetime) -> int:
        stmt = select(func.count(User.id)).where(User.created_at >= date_limit)
        return self.db.scalar(stmt) or 0

    def count_users_created_between(self, start: datetime, end: datetime) -> int:
        stmt = select(func.count(User.id)).where(and_(User.created_at >= start, User.created_at <= end))
        return self.db.scalar(stmt) or 0

    def get_recent_users(self, limit: int = 5) -> List[User]:
        stmt = select(User).order_by(desc(User.created_at)).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count_housing_offers(self) -> int:
        stmt = select(func.count(HousingOfferTableModel.id))
        return self.db.scalar(stmt) or 0

    def count_housing_offers_created_after(self, date_limit: datetime) -> int:
        stmt = select(func.count(HousingOfferTableModel.id)).where(HousingOfferTableModel.posted_date >= date_limit)
        return self.db.scalar(stmt) or 0

    def count_housing_offers_created_between(self, start: datetime, end: datetime) -> int:
        stmt = select(func.count(HousingOfferTableModel.id)).where(
            and_(HousingOfferTableModel.posted_date >= start, HousingOfferTableModel.posted_date <= end)
        )
        return self.db.scalar(stmt) or 0

    def get_recent_housing_offers(self, limit: int = 5) -> List[HousingOfferTableModel]:
        stmt = select(HousingOfferTableModel).order_by(desc(HousingOfferTableModel.posted_date)).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count_channels(self) -> int:
        stmt = select(func.count(Channel.id))
        return self.db.scalar(stmt) or 0

    def count_channels_created_in_range(self, start: datetime, end: datetime) -> int:
        stmt = select(func.count(Channel.id)).where(and_(Channel.created_at >= start, Channel.created_at <= end))
        return self.db.scalar(stmt) or 0

    def count_channels_by_type(self) -> List[tuple]:
        stmt = select(Channel.channel_type, func.count(Channel.id)).group_by(Channel.channel_type)
        return self.db.execute(stmt).all()

    def get_recent_channels(self, limit: int = 5) -> List[Channel]:
        stmt = select(Channel).order_by(desc(Channel.created_at)).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count_messages_created_in_range(self, start: datetime, end: datetime) -> int:
        stmt = select(func.count(Message.id)).where(and_(Message.created_at >= start, Message.created_at <= end))
        return self.db.scalar(stmt) or 0

    def get_recent_messages(self, limit: int = 5) -> List[Message]:
        stmt = select(Message).order_by(desc(Message.created_at)).limit(limit)
        return list(self.db.scalars(stmt).all())
