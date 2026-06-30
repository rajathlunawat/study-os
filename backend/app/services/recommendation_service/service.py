"""
StudyOS Recommendation Service — Main Service.

Responsibility: Orchestrates topic recommendations.
Fetches data from SyllabusService and ProgressService, formats it into
TopicCandidates, and runs it through the RecommendationEngine.
"""

from typing import List

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.services.recommendation_service.engine import (
    RecommendationEngine,
    TopicCandidate,
    RecommendedTopic,
)
# from app.services.progress_service import ProgressAnalytics (Conceptual import)
# from app.services.syllabus_service import SyllabusService (Conceptual import)

logger = get_logger(__name__)


class RecommendationService:
    """
    Public API for study recommendations.
    """

    @staticmethod
    def get_next_study_topics(
        db: Session, user_id: int, max_results: int = 3
    ) -> List[RecommendedTopic]:
        """
        Determine the optimal topics the student should study next.

        Flow:
        1. Query SyllabusService for all known topics for this user.
        2. Query ProgressService for quiz accuracy and last study dates per topic.
        3. Build a list of TopicCandidates.
        4. Use the RecommendationEngine to score and sort them.

        Args:
            db: Database session.
            user_id: The student's ID.
            max_results: Maximum number of recommendations to return.

        Returns:
            A sorted list of RecommendedTopic objects.
        """
        try:
            # ──────────────────────────────────────────────────────────────────
            # TODO: In a fully wired application, we would fetch actual data here.
            # Example:
            # syllabus_topics = SyllabusService.get_all_topics(db, user_id)
            # progress_data = ProgressAnalytics.get_topic_stats(db, user_id)
            # ──────────────────────────────────────────────────────────────────

            # For the scaffold, we simulate the data aggregation process:
            candidates = [
                TopicCandidate(
                    title="Introduction to Data Structures",
                    is_new=False,
                    quiz_accuracy=45.0,  # Low accuracy -> Needs remediation
                    last_studied_days_ago=3,
                ),
                TopicCandidate(
                    title="Binary Search Trees",
                    is_new=True,         # Never studied -> Progression
                    quiz_accuracy=None,
                    last_studied_days_ago=None,
                ),
                TopicCandidate(
                    title="Big O Notation",
                    is_new=False,
                    quiz_accuracy=92.0,  # High accuracy, but studied long ago
                    last_studied_days_ago=21, 
                ),
                TopicCandidate(
                    title="Graph Algorithms",
                    is_new=False,
                    quiz_accuracy=85.0,  # High accuracy, studied recently -> Low priority
                    last_studied_days_ago=1,
                )
            ]

            # Run the deterministic scoring engine
            recommendations = RecommendationEngine.generate_recommendations(
                candidates=candidates,
                max_results=max_results,
            )

            logger.info("Generated %d recommendations for user %d.", len(recommendations), user_id)
            return recommendations

        except Exception as e:
            logger.error(
                "Failed to generate recommendations for user %d: %s", 
                user_id, str(e)
            )
            return []
