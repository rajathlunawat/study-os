"""
StudyOS Schemas Public API.

Re-exports all Pydantic models for easy importing across the application.
"""

from .user import UserCreate, UserUpdate, UserResponse, UserBase
from .document import DocumentResponse, DocumentChunkResponse
from .quiz import QuizCreate, QuizResponse, QuizQuestionResponse
from .flashcard import FlashcardCreate, FlashcardReviewUpdate, FlashcardResponse
from .study_plan import StudyPlanCreate, StudyPlanResponse, StudyTaskResponse, StudyTaskUpdate
from .conversation import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse

__all__ = [
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserBase",
    # Document
    "DocumentResponse",
    "DocumentChunkResponse",
    # Quiz
    "QuizCreate",
    "QuizResponse",
    "QuizQuestionResponse",
    # Flashcard
    "FlashcardCreate",
    "FlashcardReviewUpdate",
    "FlashcardResponse",
    # Study Plan
    "StudyPlanCreate",
    "StudyPlanResponse",
    "StudyTaskResponse",
    "StudyTaskUpdate",
    # Conversation
    "ConversationCreate",
    "ConversationResponse",
    "MessageCreate",
    "MessageResponse",
]
