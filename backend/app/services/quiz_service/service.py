"""
StudyOS Quiz Service — Main Service.

Responsibility: Orchestrates quiz generation and persistence.
Uses the AIService for RAG-powered question generation and saves
results to the SQLite database.

Design Decision: This service is intentionally thin. The heavy lifting
(retrieval, prompt building, LLM call, JSON parsing) is handled by
AIService. QuizService's job is to:
1. Call AIService.generate_quiz() to get raw question dicts.
2. Persist the Quiz and QuizQuestion rows in SQLite.
3. Provide query methods for the API layer.
"""

from typing import List

from sqlalchemy.orm import Session

from app.core.exceptions import DocumentNotFoundError, QuizGenerationError
from app.core.logging_config import get_logger
from app.db.models.document import Document
from app.db.models.quiz import Quiz, QuizQuestion
from app.schemas.quiz import QuizCreate
from app.services.ai_service import AIService

logger = get_logger(__name__)


class QuizService:
    """
    Public API for quiz operations.
    """

    def __init__(self, ai_service: AIService | None = None):
        self.ai = ai_service or AIService()

    def generate(self, db: Session, user_id: int, quiz_in: QuizCreate) -> Quiz:
        """
        Generate a quiz from the student's notes and save it to the database.

        Args:
            db: Database session.
            user_id: The student's ID.
            quiz_in: Request payload with document_id, topic, and num_questions.

        Returns:
            The persisted Quiz ORM object with its questions loaded.

        Raises:
            DocumentNotFoundError: If a specific document_id was given but doesn't exist.
            QuizGenerationError: If the AI fails to produce valid questions.
        """
        # Validate document exists if provided
        if quiz_in.document_id:
            doc = db.query(Document).filter(Document.id == quiz_in.document_id).first()
            if not doc:
                raise DocumentNotFoundError(document_id=str(quiz_in.document_id))

        # Derive a title for the quiz
        title = f"Quiz: {quiz_in.topic}" if quiz_in.topic else "Generated Quiz"

        try:
            # Delegate to AIService for the RAG pipeline
            raw_questions = self.ai.generate_quiz(
                db=db,
                user_id=user_id,
                num_questions=quiz_in.num_questions,
                document_id=quiz_in.document_id,
                topic=quiz_in.topic,
            )
        except Exception as e:
            raise QuizGenerationError(
                message="Failed to generate quiz questions.",
                details={"error": str(e)}
            ) from e

        if not raw_questions:
            raise QuizGenerationError(message="AI returned no questions.")

        # Persist Quiz
        db_quiz = Quiz(
            user_id=user_id,
            document_id=quiz_in.document_id,
            title=title,
        )
        db.add(db_quiz)
        db.flush()  # Get the quiz ID before adding questions

        # Persist QuizQuestions
        for q_data in raw_questions:
            question = QuizQuestion(
                quiz_id=db_quiz.id,
                question=q_data.get("question", ""),
                correct_answer=q_data.get("correct_answer", ""),
                explanation=q_data.get("explanation"),
            )
            # Use the property setter to JSON-encode options
            question.options = q_data.get("options", [])
            db.add(question)

        db.commit()
        db.refresh(db_quiz)

        logger.info(
            "Quiz %d created for user %d with %d questions.",
            db_quiz.id, user_id, len(raw_questions)
        )

        return db_quiz

    @staticmethod
    def get_by_id(db: Session, quiz_id: int) -> Quiz | None:
        """
        Retrieve a quiz by its ID, including nested questions.
        """
        return db.query(Quiz).filter(Quiz.id == quiz_id).first()

    @staticmethod
    def get_by_user(db: Session, user_id: int) -> List[Quiz]:
        """
        Retrieve all quizzes for a given user, ordered by most recent first.
        """
        return (
            db.query(Quiz)
            .filter(Quiz.user_id == user_id)
            .order_by(Quiz.created_at.desc())
            .all()
        )
