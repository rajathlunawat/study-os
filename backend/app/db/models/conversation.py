"""
StudyOS DB Models — Conversation.

Responsibility: Defines the SQLAlchemy ORM models for the `conversation` 
and `message` tables for AI chat tracking.
Contains no business logic, only the schema definition and relationships.
"""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Conversation(Base):
    """
    Represents an ongoing or past chat session with the AI assistant.
    
    Attributes:
        id: Primary key.
        user_id: Foreign key linking to the student.
        title: Auto-generated title summarizing the conversation topic.
        created_at: Timestamp of when the chat started (UTC).
    """
    __tablename__ = "conversation"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), default="New Conversation")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    
    # A conversation holds a sequence of messages
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    """
    Represents a single turn in a Conversation.
    
    Attributes:
        id: Primary key.
        conversation_id: Foreign key linking to the parent Conversation.
        role: The speaker's identity ('user', 'assistant', 'system').
        content: The actual text of the message.
        created_at: Timestamp when the message was sent (UTC).
    """
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversation.id"), index=True, nullable=False)
    
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    # ── Relationships ─────────────────────────────────────────────────────────
    
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
