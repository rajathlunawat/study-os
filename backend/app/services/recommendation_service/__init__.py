"""
StudyOS Recommendation Service Public API.
"""

from .service import RecommendationService
from .engine import RecommendationEngine, RecommendedTopic, TopicCandidate

__all__ = [
    "RecommendationService",
    "RecommendationEngine",
    "RecommendedTopic",
    "TopicCandidate",
]
