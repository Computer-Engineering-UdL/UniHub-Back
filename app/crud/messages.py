import datetime
import uuid
from typing import List

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.crud.utils import handle_crud_errors
from app.models import Message
from app.schemas import MessageAnswer, MessageCreate, MessageUpdate


class MessagesCRUD:
    @staticmethod
    @handle_crud_errors
    def get_message_by_id(
        db: Session,
        message_id: uuid.UUID,
    ) -> Message:
        query = db.query(Message)
        if message_id is None:
            raise NoResultFound("Message not found")
        db_message = query.filter(Message.id == message_id).one_or_none()
        if db_message is None:
            raise NoResultFound("Message not found")

        return db_message

    @staticmethod
    @handle_crud_errors
    def get_channel_messages(db: Session, channel_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Message]:
        query = db.query(Message)
        if channel_id is None:
            raise NoResultFound("Channel not found")
        query = query.filter(Message.channel_id == channel_id)
        messages = query.offset(skip).limit(limit).all()
        return messages

    @staticmethod
    @handle_crud_errors
    def get_user_messages(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
        query = db.query(Message)
        if user_id is None:
            raise NoResultFound("User not found")
        query = query.filter(Message.user_id == user_id)
        messages = query.offset(skip).limit(limit).all()
        return messages

    @staticmethod
    @handle_crud_errors
    def send_message(db: Session, message: MessageCreate) -> Message:
        message_db = Message(**message.model_dump())
        db.add(message_db)
        db.commit()
        db.refresh(message_db)
        return message_db

    @staticmethod
    @handle_crud_errors
    def delete_message(db: Session, message: Message):
        db_message = db.query(Message).filter(Message.id == message.id).one_or_none()
        if db_message is None:
            raise NoResultFound("Message not found")
        db.delete(db_message)
        db.commit()

    @staticmethod
    @handle_crud_errors
    def update_message(db: Session, message_id: uuid.UUID, message_update: MessageUpdate) -> Message:
        db_message = db.query(Message).filter(Message.id == message_id).one_or_none()
        if db_message is None:
            raise NoResultFound("Message not found")
        update_data = message_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_message, key, value)
        db_message.is_edited = True
        db_message.updated_at = datetime.datetime.now(datetime.UTC)
        db.commit()
        db.refresh(db_message)
        return db_message

    @staticmethod
    @handle_crud_errors
    def answer_to_message(db: Session, message: MessageAnswer) -> Message:
        if message.parent_message_id is None:
            raise NoResultFound("Parent message not found")
        db_message = db.query(Message).filter(Message.id == message.parent_message_id).one_or_none()
        if db_message is None:
            raise NoResultFound("Message not found")
        new_message = Message(**message.model_dump())
        new_message.parent_message_id = message.parent_message_id
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        return new_message
