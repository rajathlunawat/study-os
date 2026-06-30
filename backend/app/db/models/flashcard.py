"""
StudyOS DB Models — Flashcard.

Responsibility: Defines the SQLAlchemy ORM model for the `flashcard` table.
Contains no business logic, only the schema definition and relationships.
"""

from datetime import datetime, timezone
from sqlalchemy import Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Flashcard(Base):
    """
    Represents a spaced-repetition flashcard linked to a user.
    Uses fields required for the SuperMemo-2 (SM-2) scheduling algorithm.
    
    Attributes:
        id: Primary key.
        user_id: Foreign key linking to the student.
        document_id: Optional foreign key if generated from a specific note.
        front: The question or prompt side of the card.
        back: The answer or explanation side of the card.
        next_review: UTC timestamp for when this card is due next.
        ease_factor: SM-2 difficulty multiplier (default 2.5).
        interval: Days until the next review.
        repetitions: How many times the card has been successfully recalled in a row.
    """
    __tablename__ = "flashcard"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, nullable=False)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("document.id"), index=True, nullable=True)
    
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    
    # ── Spaced Repetition Fields (SM-2) ───────────────────────────────────────
    
    next_review: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)

    # ── Relationships ─────────────────────────────────────────────────────────
    
    user: Mapped["User"] = relationship("User", back_populates="flashcards")
    document: Mapped["Document"] = relationship("Document", back_populates="flashcards")
