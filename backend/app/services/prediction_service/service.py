"""
StudyOS Prediction Service — Main Service.

Responsibility: Orchestrates the prediction flow by passing raw DB data
to the feature extractor, and feeding those features to the math model.
"""

from typing import Dict, Any

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.services.prediction_service.features import FeatureExtractor
from app.services.prediction_service.model import ReadinessModel

logger = get_logger(__name__)


class PredictionService:
    """
    Public API for predicting exam readiness.
    """

    @staticmethod
    def predict_exam_readiness(
        db: Session, user_id: int, document_id: int | None = None
    ) -> Dict[str, Any]:
        """
        Calculate the student's exam readiness.

        Args:
            db: Database session.
            user_id: The student's ID.
            document_id: (Optional) If provided, scopes the readiness prediction 
                         to a specific syllabus/subject.

        Returns:
            A dictionary containing the readiness score (0-100), a qualitative 
            band (e.g., 'On Track'), and actionable text insights.
        """
        try:
            # 1. Extract and normalize features from raw data
            features = FeatureExtractor.extract_features(db, user_id, document_id)
            
            # 2. Feed features into the math model
            result = ReadinessModel.predict(features)
            
            logger.info(
                "Predicted readiness for user %d: %s%% (%s)", 
                user_id, result["readiness_score"], result["readiness_band"]
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to predict readiness for user %d: %s", 
                user_id, str(e)
            )
            return {
                "error": "Failed to calculate readiness score.",
                "readiness_score": 0.0,
                "readiness_band": "Unknown",
                "insights": []
            }
