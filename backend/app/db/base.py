"""
StudyOS DB — Models Registration.

Import all models here so that they are registered with SQLAlchemy's
metadata. This allows `Base.metadata.create_all()` to find all tables.
"""

# Import the declarative base
from app.db.base_class import Base

# Import all models
from app.db.models.user import User
from app.db.models.document import Document, DocumentChunk
from app.db.models.quiz import Quiz, QuizQuestion
from app.db.models.flashcard import Flashcard
from app.db.models.study_plan import StudyPlan, StudyTask
from app.db.models.conversation import Conversation, Message

__all__ = [
    "Base",
    "User",
    "Document",
    "DocumentChunk",
    "Quiz",
    "QuizQuestion",
    "Flashcard",
    "StudyPlan",
    "StudyTask",
    "Conversation",
    "Message",
]
