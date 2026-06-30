"""
StudyOS Prediction Service — Feature Extractor.

Responsibility: Extracts and normalizes raw database metrics into a 
standardized feature vector for the prediction model.

Design Decision: To predict exam readiness accurately, we need to combine 
three dimensions:
1. Knowledge (Quiz accuracy, Flashcard mastery)
2. Consistency (Study streaks, task completion)
3. Coverage (How much of the syllabus has been studied)

This file normalizes all these metrics into a 0.0 to 1.0 scale.
"""

from dataclasses import dataclass
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.services.progress_service import ProgressAnalytics, ProgressTracker
# from app.services.syllabus_service import SyllabusService # (Conceptual import for coverage)


@dataclass
class ReadinessFeatures:
    """
    Normalized feature vector for exam readiness prediction.
    All values are floats between 0.0 and 1.0.
    """
    quiz_accuracy: float
    flashcard_mastery: float
    task_completion: float
    consistency_score: float
    syllabus_coverage: float


class FeatureExtractor:
    """
    Extracts raw progress data and scales it for the prediction model.
    """

    @staticmethod
    def extract_features(db: Session, user_id: int, document_id: int | None = None) -> ReadinessFeatures:
        """
        Pull metrics across all services and normalize them to [0, 1].
        """
        # 1. Knowledge Metrics
        raw_accuracy = ProgressAnalytics.calculate_quiz_accuracy(db, user_id)
        norm_accuracy = min(max(raw_accuracy / 100.0, 0.0), 1.0)

        flashcard_stats = ProgressAnalytics.get_flashcard_mastery(db, user_id)
        raw_mastery = flashcard_stats.get("mastery_rate", 0.0)
        norm_mastery = min(max(raw_mastery / 100.0, 0.0), 1.0)

        # 2. Consistency Metrics
        task_stats = ProgressAnalytics.get_task_completion_rate(db, user_id)
        raw_completion = task_stats.get("completion_rate", 0.0)
        norm_completion = min(max(raw_completion / 100.0, 0.0), 1.0)

        # We assume a 14-day streak is "perfect" consistency (1.0)
        streak = ProgressTracker.log_study_activity(db, user_id)
        norm_streak = min(streak / 14.0, 1.0)

        # 3. Coverage Metric
        # In a full implementation, we'd call SyllabusService to get the exact 
        # coverage for the specific document_id (if provided).
        # For this scaffold, we simulate a 65% coverage rate.
        norm_coverage = 0.65 

        return ReadinessFeatures(
            quiz_accuracy=norm_accuracy,
            flashcard_mastery=norm_mastery,
            task_completion=norm_completion,
            consistency_score=norm_streak,
            syllabus_coverage=norm_coverage,
        )
