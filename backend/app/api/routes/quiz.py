"""
StudyOS API — Quiz Routes.

Responsibility: Endpoints for generating and fetching quizzes.
Delegates logic to QuizService.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db_session
from app.schemas.quiz import QuizCreate, QuizResponse

router = APIRouter()


@router.post("/generate", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def generate_quiz(
    user_id: int,
    quiz_in: QuizCreate,
    db: Session = Depends(get_db_session)
) -> QuizResponse:
    """
    Generate a new quiz based on a document or topic using AI.
    """
    # TODO: Delegate to quiz_service.generate(db, user_id, quiz_in)
    raise HTTPException(status_code=501, detail="QuizService not yet implemented")


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db_session)
) -> QuizResponse:
    """
    Retrieve a previously generated quiz and its questions.
    """
    # TODO: Delegate to quiz_service.get(db, quiz_id)
    raise HTTPException(status_code=501, detail="QuizService not yet implemented")
