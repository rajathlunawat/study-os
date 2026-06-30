"""
StudyOS API — User Routes.

Responsibility: Endpoints for user management.
Delegates business logic to UserService (to be implemented).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db_session
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate, 
    db: Session = Depends(get_db_session)
) -> UserResponse:
    """
    Create a new user.
    """
    # TODO: Delegate to user_service.create(db, user_in)
    raise HTTPException(status_code=501, detail="UserService not yet implemented")


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int, 
    db: Session = Depends(get_db_session)
) -> UserResponse:
    """
    Get a specific user by ID.
    """
    # TODO: Delegate to user_service.get(db, user_id)
    raise HTTPException(status_code=501, detail="UserService not yet implemented")
