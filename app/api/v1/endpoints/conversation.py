import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from app.api.utils import handle_api_errors
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.types import TokenData
from app.crud.conversation import ConversationCRUD
from app.schemas import (
    ConversationCreate,
    ConversationDetail,
    ConversationMessageCreate,
    ConversationMessageRead,
    ConversationRead,
)

router = APIRouter()


@router.post("/", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
@handle_api_errors()
def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    Create a new conversation or get existing one.
    Optionally link to a housing offer and send initial message.
    """
    if conversation.other_user_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create conversation with yourself",
        )

    return ConversationCRUD.create_conversation(db, user.id, conversation)


@router.get("/", response_model=List[ConversationRead])
@handle_api_errors()
def get_my_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    Get all conversations for the current user.
    Ordered by most recent message.
    """
    conversations = ConversationCRUD.get_user_conversations(db, user.id, skip, limit)

    result = []
    for conv in conversations:
        unread_count = ConversationCRUD.get_unread_count(db, conv.id, user.id)
        last_message = None
        if conv.messages:
            last_message = conv.messages[-1].content[:100]

        conv_dict = {
            "id": conv.id,
            "user1_id": conv.user1_id,
            "user2_id": conv.user2_id,
            "housing_offer_id": conv.housing_offer_id,
            "created_at": conv.created_at,
            "last_message_at": conv.last_message_at,
            "unread_count": unread_count,
            "last_message": last_message,
        }
        result.append(ConversationRead(**conv_dict))

    return result


@router.get("/{conversation_id}", response_model=ConversationDetail)
@handle_api_errors()
def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    Get a specific conversation with all messages.
    User must be a participant.
    """
    conversation = ConversationCRUD.get_conversation_by_id(db, conversation_id, user.id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    ConversationCRUD.mark_messages_as_read(db, conversation_id, user.id)

    return conversation


@router.post("/{conversation_id}/messages", response_model=ConversationMessageRead)
@handle_api_errors()
def send_message(
    conversation_id: uuid.UUID,
    message: ConversationMessageCreate,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    Send a message in a conversation.
    User must be a participant.
    """
    conversation = ConversationCRUD.get_conversation_by_id(db, conversation_id, user.id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return ConversationCRUD.send_message(db, conversation_id, user.id, message)


@router.get("/{conversation_id}/messages", response_model=List[ConversationMessageRead])
@handle_api_errors()
def get_conversation_messages(
    conversation_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    Get messages from a conversation.
    User must be a participant.
    """
    conversation = ConversationCRUD.get_conversation_by_id(db, conversation_id, user.id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return ConversationCRUD.get_conversation_messages(db, conversation_id, skip, limit)


@router.post("/{conversation_id}/mark-read", status_code=status.HTTP_204_NO_CONTENT)
@handle_api_errors()
def mark_conversation_read(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    Mark all messages in a conversation as read.
    User must be a participant.
    """
    conversation = ConversationCRUD.get_conversation_by_id(db, conversation_id, user.id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    ConversationCRUD.mark_messages_as_read(db, conversation_id, user.id)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_api_errors()
def delete_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    Delete a conversation.
    User must be a participant.
    """
    success = ConversationCRUD.delete_conversation(db, conversation_id, user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
