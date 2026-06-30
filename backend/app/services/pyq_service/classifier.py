"""
StudyOS PYQ Service — Question Classifier.

Responsibility: Maps an extracted exam question to a specific syllabus topic.

Design Decision: We use the existing FAISS semantic search from RetrievalService.
Since syllabus topics were already embedded and stored in FAISS (during the
syllabus parsing phase), we can embed the question text and find the closest
matching syllabus topic chunk. This is deterministic, fast, and uses 0 LLM tokens.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.db.models.document import DocumentChunk
from app.services.retrieval_service import RetrievalService
from app.services.pyq_service.extractor import ExtractedQuestion

logger = get_logger(__name__)


class QuestionClassifier:
    """
    Classifies PYQs by matching them against the student's knowledge base.
    """

    @staticmethod
    def classify(
        db: Session, 
        user_id: int, 
        question: ExtractedQuestion,
        top_k: int = 1
    ) -> Optional[str]:
        """
        Match an extracted question to the closest topic in the knowledge base.

        Args:
            db: Database session.
            user_id: The student's ID (scopes FAISS search).
            question: The extracted question to classify.
            top_k: Number of matches to consider (default 1 for strict mapping).

        Returns:
            The title/text of the closest matching topic or chunk, 
            or None if no match is found.
        """
        try:
            # We only use the question text for semantic matching, 
            # ignoring the question number and marks.
            matched_chunks: List[DocumentChunk] = RetrievalService.semantic_search(
                db=db,
                user_id=user_id,
                query=question.text,
                top_k=top_k,
            )

            if matched_chunks:
                # Return a truncated preview of the best matching chunk
                # In a full implementation, we would map this back to a specific SyllabusTopic
                best_match = matched_chunks[0].text
                return best_match[:100] + "..." if len(best_match) > 100 else best_match
            
            return None

        except Exception as e:
            logger.warning(
                "Failed to classify question '%s' for user %d: %s",
                question.number_label, user_id, str(e)
            )
            return None
