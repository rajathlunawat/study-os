"""
StudyOS Agents — Tutor Agent.

Responsibility: Acts as a conversational mentor. 
Coordinates PredictionService and RecommendationService to provide
personalized, data-driven advice to the student via chat.
"""

from typing import Dict, Any

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.agents.base import BaseAgent
from app.services.prediction_service import PredictionService
from app.services.recommendation_service import RecommendationService

logger = get_logger(__name__)


class TutorAgent(BaseAgent):
    """
    A proactive study mentor that grounds its advice in the user's actual progress data.
    """

    @property
    def persona(self) -> str:
        return (
            "You are StudyOS Tutor, a supportive AI mentor. "
            "You have access to the student's exam readiness score and "
            "recommended topics. Use this data to provide highly personalized, "
            "actionable advice. Be concise and encouraging."
        )

    def process_message(self, db: Session, user_id: int, message: str) -> Dict[str, Any]:
        """
        Respond to the user by injecting their current study stats into the LLM prompt.
        """
        logger.info("TutorAgent processing message for user %d", user_id)
        
        # 1. Fetch live metrics from services
        readiness_data = PredictionService.predict_exam_readiness(db, user_id)
        recommendations = RecommendationService.get_next_study_topics(db, user_id, max_results=2)

        # 2. Format the metrics to ground the LLM
        rec_text = "\n".join([f"- {r.title} ({r.reason})" for r in recommendations])
        if not rec_text:
            rec_text = "No specific recommendations at this time."

        context_injection = (
            f"\n\n--- STUDENT DATA ---\n"
            f"Readiness Score: {readiness_data.get('readiness_score', 'N/A')}%\n"
            f"Current Status: {readiness_data.get('readiness_band', 'N/A')}\n"
            f"Recommended Next Topics:\n{rec_text}\n"
            f"----------------------\n"
        )

        # 3. Build the prompt
        prompt = f"{self.persona}{context_injection}\nStudent says: {message}\n\nTutor:"

        # 4. Generate response
        response_text = self.llm.generate(prompt)

        return {
            "response": response_text,
            "actions": ["fetched_metrics"],
            "readiness_score": readiness_data.get("readiness_score")
        }
