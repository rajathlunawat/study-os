"""
StudyOS Agents — Manager.

Responsibility: Routes user chat messages to the correct specialized service 
or agent based on intent classification.
"""

from typing import Dict, Any

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.agents.tutor_agent import TutorAgent
from app.services.ai_service import LLMClient

logger = get_logger(__name__)


class AgentManager:
    """
    Central orchestrator for the conversational interface.
    Decides whether a user input requires a specific service action 
    (like creating a quiz) or general mentoring (routing to TutorAgent).
    """

    def __init__(self):
        self.llm = LLMClient()
        self.tutor = TutorAgent(llm_client=self.llm)

    def route_request(self, db: Session, user_id: int, message: str) -> Dict[str, Any]:
        """
        Classify intent and route to the appropriate handler.
        """
        intent = self._classify_intent(message)
        logger.info("AgentManager classified intent '%s' for user %d", intent, user_id)

        if intent == "QUIZ_REQUEST":
            # Here we would normally extract the topic and call QuizService
            return {
                "response": "I see you want a quiz. I'm routing you to the quiz generator.",
                "action": "trigger_quiz_workflow"
            }
            
        elif intent == "STUDY_PLAN_REQUEST":
            # Here we would extract the topic/date and call PlannerService
            return {
                "response": "Let's build a study plan for you. What topic are you studying?",
                "action": "trigger_planner_workflow"
            }
            
        else:
            # Default to conversational mentoring
            return self.tutor.process_message(db, user_id, message)

    def _classify_intent(self, message: str) -> str:
        """
        Uses simple keyword heuristics (or a very cheap LLM call) to classify the user's intent.
        For a low-RAM, fast application, heuristics are preferred before invoking an LLM.
        """
        msg_lower = message.lower()
        
        if "quiz" in msg_lower or "test me" in msg_lower:
            return "QUIZ_REQUEST"
            
        if "plan" in msg_lower or "schedule" in msg_lower:
            return "STUDY_PLAN_REQUEST"
            
        return "GENERAL_CHAT"
