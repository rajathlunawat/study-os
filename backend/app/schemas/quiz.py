"""
StudyOS Schemas — Quiz.

Responsibility: Defines the Pydantic models for Quizzes and Questions.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ── Quiz Question Schemas ─────────────────────────────────────────────────────

class QuizQuestionResponse(BaseModel):
    """
    Response schema for a single quiz question.
    """
    id: int
    quiz_id: int
    question: str
    options: list[str] = Field(..., description="Decoded list of multiple-choice options.")
    correct_answer: str
    explanation: str | None = Field(None, description="AI reasoning for the correct answer.")

    model_config = ConfigDict(from_attributes=True)


# ── Quiz Schemas ──────────────────────────────────────────────────────────────

class QuizCreate(BaseModel):
    """
    Request payload to generate a new quiz.
    """
    document_id: int | None = Field(None, description="Optional document to base the quiz on.")
    topic: str | None = Field(None, description="Topic to generate the quiz about if no document is provided.")
    num_questions: int = Field(5, ge=1, le=20, description="Number of questions to generate (1-20).")


class QuizResponse(BaseModel):
    """
    Response schema for a Quiz, optionally including its nested questions.
    """
    id: int
    user_id: int
    document_id: int | None
    title: str
    created_at: datetime
    questions: list[QuizQuestionResponse] = Field(
        default_factory=list, description="Nested list of questions."
    )

    model_config = ConfigDict(from_attributes=True)
