"""
StudyOS API — Conversation Routes.

Responsibility: Endpoints for AI chat conversations and RAG messaging.
Delegates logic to ConversationService.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db_session
from app.schemas.conversation import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse

router = APIRouter()


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def start_conversation(
    user_id: int,
    conversation_in: ConversationCreate,
    db: Session = Depends(get_db_session)
) -> ConversationResponse:
    """
    Start a new chat conversation with the AI.
    """
    # TODO: Delegate to conversation_service.start(db, user_id, conversation_in)
    raise HTTPException(status_code=501, detail="ConversationService not yet implemented")


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
def send_message(
    conversation_id: int,
    message_in: MessageCreate,
    db: Session = Depends(get_db_session)
) -> MessageResponse:
    """
    Send a message to the AI and receive a response.
    This endpoint will trigger the RAG pipeline.
    """
    # TODO: Delegate to conversation_service.send_message(db, conversation_id, message_in)
    raise HTTPException(status_code=501, detail="ConversationService not yet implemented")


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation_history(
    conversation_id: int,
    db: Session = Depends(get_db_session)
) -> ConversationResponse:
    """
    Fetch the entire history of a specific conversation.
    """
    # TODO: Delegate to conversation_service.get(db, conversation_id)
    raise HTTPException(status_code=501, detail="ConversationService not yet implemented")
