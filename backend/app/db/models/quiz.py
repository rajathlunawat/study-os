"""
StudyOS DB Models — Quiz.

Responsibility: Defines the SQLAlchemy ORM models for the `quiz` 
and `quiz_question` tables.
Contains no business logic, only the schema definition and relationships.
"""

import json
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Quiz(Base):
    """
    Represents an AI-generated quiz linked to a specific user and document.
    
    Attributes:
        id: Primary key.
        user_id: Foreign key linking the quiz to a student.
        document_id: Optional foreign key if the quiz is based on a specific note.
        title: Title of the quiz.
        created_at: Timestamp of generation (UTC).
    """
    __tablename__ = "quiz"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, nullable=False)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("document.id"), index=True, nullable=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    
    user: Mapped["User"] = relationship("User", back_populates="quizzes")
    document: Mapped["Document"] = relationship("Document", back_populates="quizzes")
    
    # A quiz contains multiple questions
    questions: Mapped[list["QuizQuestion"]] = relationship(
        "QuizQuestion", back_populates="quiz", cascade="all, delete-orphan"
    )


class QuizQuestion(Base):
    """
    Represents a single multiple-choice question within a Quiz.
    
    Attributes:
        id: Primary key.
        quiz_id: Foreign key linking to the parent Quiz.
        question: The text of the question.
        options_json: A JSON-encoded list of possible answers.
        correct_answer: The exact string of the correct option.
        explanation: AI-generated reasoning for the correct answer.
    """
    __tablename__ = "quiz_question"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quiz.id"), index=True, nullable=False)
    
    question: Mapped[str] = mapped_column(Text, nullable=False)
    options_json: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # ── Relationships ─────────────────────────────────────────────────────────
    
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")

    # Property wrappers to handle JSON serialization (Not business logic, just schema utility)
    @property
    def options(self) -> list[str]:
        return json.loads(self.options_json)
        
    @options.setter
    def options(self, value: list[str]) -> None:
        self.options_json = json.dumps(value)
