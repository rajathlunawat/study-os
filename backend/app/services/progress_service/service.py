"""
StudyOS Progress Service — Main Service.

Responsibility: Orchestrates progress tracking and analytics fetching.
Provides a unified interface for the API layer to fetch the student's dashboard stats.
"""

from typing import Dict, Any

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.services.progress_service.analytics import ProgressAnalytics
from app.services.progress_service.tracker import ProgressTracker

logger = get_logger(__name__)


class ProgressService:
    """
    Public API for study progress and analytics.
    """

    @staticmethod
    def get_user_dashboard_stats(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Aggregate all progress metrics for the main student dashboard.

        Args:
            db: Database session.
            user_id: The student's ID.

        Returns:
            A dictionary containing completion rates, mastery stats, and streaks.
        """
        try:
            # Fetch various metrics
            task_stats = ProgressAnalytics.get_task_completion_rate(db, user_id)
            flashcard_stats = ProgressAnalytics.get_flashcard_mastery(db, user_id)
            quiz_accuracy = ProgressAnalytics.calculate_quiz_accuracy(db, user_id)
            
            # Fetch streak (simulated lookup via tracker logic)
            # A true fetch would just read `user.current_streak`
            current_streak = ProgressTracker.log_study_activity(db, user_id)

            return {
                "user_id": user_id,
                "current_streak": current_streak,
                "quiz_accuracy_percent": quiz_accuracy,
                "study_tasks": task_stats,
                "flashcards": flashcard_stats,
            }
            
        except Exception as e:
            logger.error("Failed to fetch dashboard stats for user %d: %s", user_id, str(e))
            return {
                "error": "Failed to load dashboard statistics."
            }

    @staticmethod
    def log_activity(db: Session, user_id: int) -> int:
        """
        Triggered when a user completes a meaningful action 
        (e.g., finishes a quiz, completes a study task).
        """
        return ProgressTracker.log_study_activity(db, user_id)
