"""
StudyOS Schemas — Flashcard.

Responsibility: Defines the Pydantic models for Flashcards.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ── Create & Update Schemas ───────────────────────────────────────────────────

class FlashcardCreate(BaseModel):
    """
    Request payload to manually create a flashcard or trigger AI generation.
    """
    document_id: int | None = Field(None, description="Optional document to link the flashcard to.")
    front: str = Field(..., description="The question or prompt.")
    back: str = Field(..., description="The answer or explanation.")


class FlashcardReviewUpdate(BaseModel):
    """
    Request payload sent when a user reviews a flashcard.
    The 'score' determines the next SM-2 interval.
    Typically: 0 (Blackout) to 5 (Perfect response).
    """
    score: int = Field(..., ge=0, le=5, description="SM-2 recall quality score (0-5).")


# ── Response Schema ───────────────────────────────────────────────────────────

class FlashcardResponse(BaseModel):
    """
    Response schema representing a flashcard and its spaced-repetition state.
    """
    id: int
    user_id: int
    document_id: int | None
    front: str
    back: str
    
    next_review: datetime = Field(..., description="When the card should be reviewed next.")
    ease_factor: float
    interval: int
    repetitions: int

    model_config = ConfigDict(from_attributes=True)
