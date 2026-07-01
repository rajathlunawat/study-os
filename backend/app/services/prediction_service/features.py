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

from app.database import get_user_stats
from dataclasses import dataclass

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
    def extract_features(db=None, user_id: int = 1, document_id: int | None = None) -> ReadinessFeatures:
        """
        Pull metrics across all services and normalize them to [0, 1].
        """
        stats = get_user_stats()
        if not stats:
            stats = {
                "quiz_accuracy": 0.5,
                "flashcard_mastery": 0.5,
                "task_completion": 0.5,
                "consistency_score": 0.5,
                "study_streak": 0
            }

        norm_accuracy = min(max(stats["quiz_accuracy"], 0.0), 1.0)
        norm_mastery = min(max(stats["flashcard_mastery"], 0.0), 1.0)
        norm_completion = min(max(stats["task_completion"], 0.0), 1.0)
        
        # We assume a 14-day streak is "perfect" consistency (1.0)
        norm_streak = min(stats["study_streak"] / 14.0, 1.0)
        norm_consistency = max(norm_streak, stats["consistency_score"])

        # 3. Coverage Metric
        # For this scaffold, we simulate a 65% coverage rate.
        norm_coverage = 0.65 

        return ReadinessFeatures(
            quiz_accuracy=norm_accuracy,
            flashcard_mastery=norm_mastery,
            task_completion=norm_completion,
            consistency_score=norm_consistency,
            syllabus_coverage=norm_coverage,
        )
