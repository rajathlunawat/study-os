"""
StudyOS DB Models — User.

Responsibility: Defines the SQLAlchemy ORM model for the `user` table.
Contains no business logic, only the schema definition and relationships.
"""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

# We import Base from our db setup
from app.db.base_class import Base


class User(Base):
    """
    Represents a student or user of StudyOS.
    
    Attributes:
        id: Primary key.
        name: The user's full or display name.
        email: Optional email address (unique).
        created_at: Timestamp of account creation (UTC).
    """
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    
    # A user can upload many documents
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="user", cascade="all, delete-orphan"
    )
    
    # A user can generate many quizzes
    quizzes: Mapped[list["Quiz"]] = relationship(
        "Quiz", back_populates="user", cascade="all, delete-orphan"
    )
    
    # A user has many flashcards for spaced repetition
    flashcards: Mapped[list["Flashcard"]] = relationship(
        "Flashcard", back_populates="user", cascade="all, delete-orphan"
    )
    
    # A user can create many study plans
    study_plans: Mapped[list["StudyPlan"]] = relationship(
        "StudyPlan", back_populates="user", cascade="all, delete-orphan"
    )
    
    # A user can have many AI chat conversations
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
