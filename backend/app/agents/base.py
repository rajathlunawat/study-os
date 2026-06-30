"""
StudyOS Agents — Base Agent Interface.

Responsibility: Defines the abstract contract for all conversational agents
in the system. Ensures agents rely on services rather than duplicating logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.services.ai_service import LLMClient


class BaseAgent(ABC):
    """
    Abstract base class for all AI Agents in StudyOS.
    """

    def __init__(self, llm_client: LLMClient | None = None):
        """
        Agents require an LLM client to parse intents and generate responses.
        We inject the client to allow easy mocking during tests.
        """
        self.llm = llm_client or LLMClient()

    @property
    @abstractmethod
    def persona(self) -> str:
        """
        The system prompt defining the agent's behavior and constraints.
        """
        pass

    @abstractmethod
    def process_message(self, db: Session, user_id: int, message: str) -> Dict[str, Any]:
        """
        Process a user's message, potentially coordinate services, and return a response.

        Args:
            db: Database session.
            user_id: The ID of the student interacting with the agent.
            message: The raw text input from the user.

        Returns:
            A dictionary containing the agent's text 'response' and any 'actions' taken.
        """
        pass
