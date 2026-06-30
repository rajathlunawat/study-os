"""
StudyOS Flashcard Service — Main Service.

Responsibility: Orchestrates flashcard generation, persistence, 
querying due cards, and applying SM-2 reviews.
"""

from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.core.exceptions import DocumentNotFoundError, QuizGenerationError
from app.core.logging_config import get_logger
from app.db.models.document import Document
from app.db.models.flashcard import Flashcard
from app.schemas.flashcard import FlashcardCreate, FlashcardReviewUpdate
from app.services.ai_service import AIService
from app.services.flashcard_service.sm2 import sm2_schedule

logger = get_logger(__name__)


class FlashcardService:
    """
    Public API for flashcard operations.
    """

    def __init__(self, ai_service: AIService | None = None):
        self.ai = ai_service or AIService()

    # ── Creation ──────────────────────────────────────────────────────────────

    def create_manual(
        self, db: Session, user_id: int, flashcard_in: FlashcardCreate
    ) -> Flashcard:
        """
        Create a single flashcard manually (student-authored, not AI-generated).
        """
        if flashcard_in.document_id:
            doc = db.query(Document).filter(Document.id == flashcard_in.document_id).first()
            if not doc:
                raise DocumentNotFoundError(document_id=str(flashcard_in.document_id))

        card = Flashcard(
            user_id=user_id,
            document_id=flashcard_in.document_id,
            front=flashcard_in.front,
            back=flashcard_in.back,
        )
        db.add(card)
        db.commit()
        db.refresh(card)

        logger.info("Manual flashcard %d created for user %d.", card.id, user_id)
        return card

    def generate_from_notes(
        self,
        db: Session,
        user_id: int,
        num_cards: int = 10,
        topic: str | None = None,
        document_id: int | None = None,
    ) -> List[Flashcard]:
        """
        Use the AI RAG pipeline to generate flashcards from the student's notes
        and persist them to the database.

        Returns:
            A list of persisted Flashcard ORM objects.
        """
        try:
            raw_cards = self.ai.generate_flashcards(
                db=db,
                user_id=user_id,
                num_cards=num_cards,
                topic=topic,
            )
        except Exception as e:
            raise QuizGenerationError(
                message="Failed to generate flashcards.",
                details={"error": str(e)}
            ) from e

        if not raw_cards:
            return []

        db_cards = []
        for card_data in raw_cards:
            card = Flashcard(
                user_id=user_id,
                document_id=document_id,
                front=card_data.get("front", ""),
                back=card_data.get("back", ""),
            )
            db.add(card)
            db_cards.append(card)

        db.commit()

        # Refresh all cards to populate IDs
        for card in db_cards:
            db.refresh(card)

        logger.info(
            "Generated %d AI flashcards for user %d.", len(db_cards), user_id
        )
        return db_cards

    # ── Review (SM-2) ────────────────────────────────────────────────────────

    @staticmethod
    def review(
        db: Session, flashcard_id: int, review_in: FlashcardReviewUpdate
    ) -> Flashcard:
        """
        Apply the SM-2 algorithm after a student reviews a flashcard.

        Args:
            db: Database session.
            flashcard_id: The ID of the reviewed flashcard.
            review_in: Contains the score (0-5).

        Returns:
            The updated Flashcard with new scheduling fields.
        """
        card = db.query(Flashcard).filter(Flashcard.id == flashcard_id).first()
        if not card:
            raise DocumentNotFoundError(
                message="Flashcard not found.",
                details={"flashcard_id": flashcard_id}
            )

        # Run the pure SM-2 algorithm
        result = sm2_schedule(
            score=review_in.score,
            current_ease=card.ease_factor,
            current_interval=card.interval,
            current_repetitions=card.repetitions,
        )

        # Apply results to the ORM object
        card.next_review = result.next_review
        card.ease_factor = result.ease_factor
        card.interval = result.interval
        card.repetitions = result.repetitions

        db.commit()
        db.refresh(card)

        logger.info(
            "Flashcard %d reviewed (score=%d). Next review in %d day(s).",
            flashcard_id, review_in.score, result.interval
        )
        return card

    # ── Queries ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_due(db: Session, user_id: int) -> List[Flashcard]:
        """
        Get all flashcards that are due for review (next_review <= now).
        """
        now = datetime.now(timezone.utc)
        return (
            db.query(Flashcard)
            .filter(
                Flashcard.user_id == user_id,
                Flashcard.next_review <= now,
            )
            .order_by(Flashcard.next_review.asc())
            .all()
        )

    @staticmethod
    def get_by_user(db: Session, user_id: int) -> List[Flashcard]:
        """
        Get all flashcards for a user, regardless of review status.
        """
        return (
            db.query(Flashcard)
            .filter(Flashcard.user_id == user_id)
            .all()
        )
