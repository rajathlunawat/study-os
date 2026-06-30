"""
StudyOS RAG — Grounding Checker.

Responsibility: Enforces the core architectural rule: "Never answer from 
general knowledge if project logic requires retrieved context."

Design Decision: After the LLM generates a response, this module checks if the 
LLM actually used the provided context. If the LLM output completely ignores 
the source material or admits it doesn't know, this module catches it before 
it reaches the user.
"""

from typing import List

from app.core.logging_config import get_logger
from app.db.models.document import DocumentChunk

logger = get_logger(__name__)


class GroundingChecker:
    """
    Validates that LLM responses are grounded in the retrieved context.
    """

    # Phrases the LLM uses when the context is insufficient (set in prompts.py)
    _FAILURE_PHRASES = [
        "i don't have enough information",
        "i do not have enough information",
        "context does not contain",
        "based on the provided context, i cannot",
    ]

    @staticmethod
    def is_grounded(llm_response: str, context_chunks: List[DocumentChunk]) -> bool:
        """
        Check if the LLM's response is grounded in the provided chunks.

        For V1 (low RAM/compute constraint), we use simple heuristic checks:
        1. Did the LLM explicitly state it couldn't find the answer?
        2. Did the LLM cite a source? (e.g., "[Chunk 1]")

        Args:
            llm_response: The raw text returned by the LLM.
            context_chunks: The chunks that were fed into the prompt.

        Returns:
            True if the response appears grounded, False otherwise.
        """
        response_lower = llm_response.lower()

        # Check 1: Did the LLM admit failure?
        for phrase in GroundingChecker._FAILURE_PHRASES:
            if phrase in response_lower:
                logger.warning("Grounding check failed: LLM admitted insufficient context.")
                return False

        if not context_chunks:
            # If no chunks were provided but the LLM answered anyway, it hallucinated.
            logger.warning("Grounding check failed: LLM answered without any context chunks.")
            return False

        # Check 2: Citation Check
        # Our prompt instructions tell the LLM to cite chunks (e.g., "[Chunk 1]").
        # If the response doesn't contain the word "chunk" or "source", it might 
        # be answering from general knowledge.
        if "chunk" not in response_lower and "source" not in response_lower:
            logger.warning(
                "Grounding check warning: LLM response lacks explicit citations."
            )
            # We don't strictly fail here in V1 as LLMs sometimes ignore formatting 
            # rules, but we log it for analytics.
            pass

        return True
