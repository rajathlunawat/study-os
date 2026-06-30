"""
StudyOS Syllabus Service — Main Service.

Responsibility: Orchestrates syllabus parsing and topic mapping.
"""

from typing import Dict, Any

from sqlalchemy.orm import Session

from app.core.exceptions import DocumentParsingError, DocumentNotFoundError
from app.core.logging_config import get_logger
from app.db.models.document import Document
from app.services.document_service import DocumentParser
from app.services.syllabus_service.topic_extractor import extract_topics
from app.services.syllabus_service.mapper import TopicMapper

logger = get_logger(__name__)


class SyllabusService:
    """
    Public API for syllabus operations.
    """

    @staticmethod
    def process_syllabus(
        db: Session, user_id: int, document_id: int
    ) -> Dict[str, Any]:
        """
        Parse an uploaded syllabus PDF, extract its topics, and map them
        against the user's other notes to determine study coverage.

        Args:
            db: Database session.
            user_id: The student's ID.
            document_id: The ID of the syllabus Document row.

        Returns:
            A dictionary containing the extracted topics and coverage stats.
            
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

        # 2. Extract raw text from the file path
        # (Re-using DocumentParser from document_service)
        try:
            from pathlib import Path
            raw_text = DocumentParser.extract_text(Path(doc.file_path))
        except Exception as e:
            raise DocumentParsingError(
                message="Failed to read syllabus file.", 
                details={"error": str(e)}
            ) from e

        # 3. Extract structured topics using deterministic regex
        topics = extract_topics(raw_text)
        logger.info("Extracted %d topics from syllabus %d", len(topics), document_id)

        # 4. Map topics to existing knowledge base
        coverage_map = TopicMapper.map_topics_to_chunks(
            db=db,
            user_id=user_id,
            topics=topics,
        )

        # 5. Calculate coverage metric
        coverage_percent = TopicMapper.calculate_coverage_percentage(coverage_map)

        # Return structured results (In a full app, these might be saved to DB)
        result = {
            "document_id": document_id,
            "total_topics": len(topics),
            "coverage_percentage": coverage_percent,
            "topics": [
                {
                    "title": t.title,
                    "unit_number": t.unit_number,
                    "subtopics": t.subtopics,
                    "is_covered": len(coverage_map.get(t.title, [])) > 0,
                    "matched_chunks": [c.id for c in coverage_map.get(t.title, [])]
                }
                for t in topics
            ]
        }
        
        return result
