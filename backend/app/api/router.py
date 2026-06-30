"""
StudyOS API — Main Router.

Responsibility: Central entry point for all API routes.
Combines all domain-specific routers under appropriate prefixes.
"""

from fastapi import APIRouter

from app.api.routes import user, document, quiz, flashcard, study_plan, conversation

api_router = APIRouter()

# Include all domain routers, assigning them appropriate path prefixes and OpenAPI tags
api_router.include_router(user.router, prefix="/users", tags=["Users"])
api_router.include_router(document.router, prefix="/documents", tags=["Documents"])
api_router.include_router(quiz.router, prefix="/quizzes", tags=["Quizzes"])
api_router.include_router(flashcard.router, prefix="/flashcards", tags=["Flashcards"])
api_router.include_router(study_plan.router, prefix="/study-plans", tags=["Study Plans"])
api_router.include_router(conversation.router, prefix="/conversations", tags=["Conversations"])
