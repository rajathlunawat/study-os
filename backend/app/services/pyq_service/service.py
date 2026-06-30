"""
StudyOS PYQ Service — Main Service.

Responsibility: Orchestrates PYQ parsing and classification.
"""

from typing import Dict, Any, List

from sqlalchemy.orm import Session

from app.core.exceptions import DocumentParsingError, DocumentNotFoundError
from app.core.logging_config import get_logger
from app.db.models.document import Document
from app.services.document_service import DocumentParser
from app.services.pyq_service.extractor import extract_questions
from app.services.pyq_service.classifier import QuestionClassifier

logger = get_logger(__name__)


class PYQService:
    """
    Public API for Previous Year Question paper operations.
    """

    @staticmethod
    def process_pyq_document(
        db: Session, user_id: int, document_id: int
    ) -> Dict[str, Any]:
        """
        Parse a PYQ PDF, extract discrete questions, and classify them.

        Args:
            db: Database session.
            user_id: The student's ID.
            document_id: The ID of the PYQ Document row.

        Returns:
            A dictionary containing the extracted and classified questions.
            
        Raises:
            DocumentNotFoundError: If the document doesn't exist.
            DocumentParsingError: If text extraction fails.
        """
        # 1. Fetch document record
        doc = db.query(Document).filter(
            Document.id == document_id, 
            Document.user_id == user_id
        ).first()
        
        if not doc:
            raise DocumentNotFoundError(document_id=str(document_id))

        # 2. Extract raw text
        try:
            from pathlib import Path
            raw_text = DocumentParser.extract_text(Path(doc.file_path))
        except Exception as e:
            raise DocumentParsingError(
                message="Failed to read PYQ file.", 
                details={"error": str(e)}
            ) from e

        # 3. Extract questions via regex
        questions = extract_questions(raw_text)
        logger.info("Extracted %d questions from PYQ %d", len(questions), document_id)

        # 4. Classify each question using FAISS
        classified_results = []
        for q in questions:
            mapped_topic = QuestionClassifier.classify(db, user_id, q)
            classified_results.append({
                "number": q.number_label,
                "question": q.text,
                "marks": q.marks,
                "mapped_topic": mapped_topic,
            })

        # 5. Return structured results
        return {
            "document_id": document_id,
            "total_questions": len(classified_results),
            "questions": classified_results
        }
