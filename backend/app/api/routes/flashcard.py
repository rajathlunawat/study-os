"""
StudyOS API — Flashcard Routes.

Responsibility: Endpoints for spaced repetition flashcards.
Delegates logic to FlashcardService.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db_session
from app.schemas.flashcard import FlashcardCreate, FlashcardResponse, FlashcardReviewUpdate

router = APIRouter()


@router.post("/", response_model=FlashcardResponse, status_code=status.HTTP_201_CREATED)
def create_flashcard(
    user_id: int,
    flashcard_in: FlashcardCreate,
    db: Session = Depends(get_db_session)
) -> FlashcardResponse:
    """
    Manually create a single flashcard.
    """
    # TODO: Delegate to flashcard_service.create(db, user_id, flashcard_in)
    raise HTTPException(status_code=501, detail="FlashcardService not yet implemented")


@router.get("/due", response_model=list[FlashcardResponse])
def get_due_flashcards(
    user_id: int,
    db: Session = Depends(get_db_session)
) -> list[FlashcardResponse]:
    """
    Get all flashcards that are due for review today for a user.
    """
    # TODO: Delegate to flashcard_service.get_due(db, user_id)
    raise HTTPException(status_code=501, detail="FlashcardService not yet implemented")


@router.patch("/{flashcard_id}/review", response_model=FlashcardResponse)
def review_flashcard(
    flashcard_id: int,
    review_in: FlashcardReviewUpdate,
    db: Session = Depends(get_db_session)
) -> FlashcardResponse:
    """
    Update a flashcard's SM-2 spaced repetition fields after a review.
    """
    # TODO: Delegate to flashcard_service.review(db, flashcard_id, review_in)
    raise HTTPException(status_code=501, detail="FlashcardService not yet implemented")
