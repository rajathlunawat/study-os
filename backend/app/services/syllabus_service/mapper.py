"""
StudyOS Syllabus Service — Mapper.

Responsibility: Maps uploaded document chunks to syllabus topics.
Uses the retrieval service (semantic search) to match study notes with
syllabus requirements to track coverage.
"""

from typing import Dict, List

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.db.models.document import DocumentChunk
from app.services.retrieval_service import RetrievalService
from app.services.syllabus_service.topic_extractor import SyllabusTopic

logger = get_logger(__name__)


class TopicMapper:
    """
    Maps document content to syllabus topics to measure study coverage.
    """

    @staticmethod
    def map_topics_to_chunks(
        db: Session,
        user_id: int,
        topics: List[SyllabusTopic],
        top_k_per_topic: int = 3,
    ) -> Dict[str, List[DocumentChunk]]:
        """
        Find the most relevant document chunks for each syllabus topic.

        Args:
            db: Database session.
            user_id: The student's ID (used to scope FAISS search).
            topics: List of topics extracted from the syllabus.
            top_k_per_topic: Number of chunks to retrieve per topic.

        Returns:
            A dictionary mapping topic titles to lists of retrieved DocumentChunks.
        """
        coverage_map = {}
        
        for topic in topics:
            # Construct a rich query using the title and subtopics
            query_parts = [topic.title]
            if topic.subtopics:
                query_parts.extend(topic.subtopics)
            
            search_query = ", ".join(query_parts)
            
            # Execute semantic search against the user's FAISS index
            try:
                matched_chunks = RetrievalService.semantic_search(
                    db=db,
                    user_id=user_id,
                    query=search_query,
                    top_k=top_k_per_topic,
                )
                coverage_map[topic.title] = matched_chunks
            except Exception as e:
                logger.warning(
                    "Failed to map topic '%s' for user %d: %s",
                    topic.title, user_id, str(e)
                )
                coverage_map[topic.title] = []

        return coverage_map

    @staticmethod
    def calculate_coverage_percentage(
        coverage_map: Dict[str, List[DocumentChunk]]
    ) -> float:
        """
        Calculate the percentage of syllabus topics that have at least one
        matching document chunk.
        
        Note: A real-world application would use a similarity threshold to
        ensure the match is high-quality, rather than just returning the top-k.
        For simplicity, if top-k returns *anything*, we consider it covered.
        """
        if not coverage_map:
            return 0.0

        covered_topics = sum(1 for chunks in coverage_map.values() if chunks)
        total_topics = len(coverage_map)

        return round((covered_topics / total_topics) * 100, 2)
