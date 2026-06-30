"""
StudyOS Schemas — Conversation.

Responsibility: Defines the Pydantic models for AI Conversations and Messages.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ── Message Schemas ───────────────────────────────────────────────────────────

class MessageCreate(BaseModel):
    """
    Request payload from the frontend to send a new message to the AI.
    """
    content: str = Field(..., min_length=1, description="The user's text input.")
    # The role is always assumed to be 'user' for incoming requests, 
    # so we do not expose it in the Create schema.


class MessageResponse(BaseModel):
    """
    Response schema for a single message in the chat history.
    """
    id: int
    conversation_id: int
    role: str = Field(..., description="Role of the sender (user, assistant, system).")
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Conversation Schemas ──────────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    """
    Request payload to start a new conversation.
    """
    title: str | None = Field(None, description="Optional title, otherwise auto-generated.")


class ConversationResponse(BaseModel):
    """
    Response schema for a Conversation, optionally including full message history.
    """
    id: int
    user_id: int
    title: str
    created_at: datetime
    messages: list[MessageResponse] = Field(
        default_factory=list, description="Chronological list of messages."
    )

    model_config = ConfigDict(from_attributes=True)
