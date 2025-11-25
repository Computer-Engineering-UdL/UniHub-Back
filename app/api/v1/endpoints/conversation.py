import uuid
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from starlette import status

from app.api.utils import handle_api_errors
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.types import TokenData
from app.domains.housing.conversation_service import ConversationService
from app.schemas import (
    ConversationCreate,
    ConversationDetail,
    ConversationMessageCreate,
    ConversationMessageRead,
    ConversationRead,
)

router = APIRouter()


async def get_conversation_service(db: Session = Depends(get_db)) -> ConversationService:
    """Dependency to inject ConversationService."""
    return ConversationService(db)


@router.post("/", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
@handle_api_errors()
async def create_conversation(
    conversation: ConversationCreate,
    service: ConversationService = Depends(get_conversation_service),
    user: TokenData = Depends(get_current_user),
):
    """
    Create a new conversation or get existing one.
    Optionally link to a housing offer and send initial message.
    """
    return service.create_conversation(user.id, conversation)


@router.get("/", response_model=List[ConversationRead])
@handle_api_errors()
async def get_my_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ConversationService = Depends(get_conversation_service),
    user: TokenData = Depends(get_current_user),
):
    """
    Get all conversations for the current user.
    Ordered by most recent message.
    """
    return service.get_user_conversations(user.id, skip, limit)


@router.get("/{conversation_id}", response_model=ConversationDetail)
@handle_api_errors()
async def get_conversation(
    conversation_id: uuid.UUID,
    service: ConversationService = Depends(get_conversation_service),
    user: TokenData = Depends(get_current_user),
):
    """
    Get a specific conversation with all messages.
    User must be a participant.
    """
    return service.get_conversation_by_id(conversation_id, user.id)


@router.post("/{conversation_id}/messages", response_model=ConversationMessageRead)
@handle_api_errors()
async def send_message(
    conversation_id: uuid.UUID,
    message: ConversationMessageCreate,
    service: ConversationService = Depends(get_conversation_service),
    user: TokenData = Depends(get_current_user),
):
    """
    Send a message in a conversation.
    User must be a participant.
    """
    return await service.send_message(conversation_id, user.id, message)


@router.get("/{conversation_id}/messages", response_model=List[ConversationMessageRead])
@handle_api_errors()
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    service: ConversationService = Depends(get_conversation_service),
    user: TokenData = Depends(get_current_user),
):
    """
    Get messages from a conversation.
    User must be a participant.
    """
    return service.get_conversation_messages(conversation_id, user.id, skip, limit)


@router.post("/{conversation_id}/mark-read", status_code=status.HTTP_204_NO_CONTENT)
@handle_api_errors()
async def mark_conversation_read(
    conversation_id: uuid.UUID,
    service: ConversationService = Depends(get_conversation_service),
    user: TokenData = Depends(get_current_user),
):
    """
    Mark all messages in a conversation as read.
    User must be a participant.
    """
    service.mark_conversation_read(conversation_id, user.id)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_api_errors()
async def delete_conversation(
    conversation_id: uuid.UUID,
    service: ConversationService = Depends(get_conversation_service),
    user: TokenData = Depends(get_current_user),
):
    """
    Delete a conversation.
    User must be a participant.
    """
    service.delete_conversation(conversation_id, user.id)
