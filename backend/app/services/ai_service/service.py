"""
StudyOS AI Service — Main Service.

Responsibility: Orchestrates the full RAG pipeline.
Combines retrieval, prompt building, LLM generation, and response parsing
into high-level methods that the API routers can call.

Design Decision: This service enforces the retrieval-first principle.
Every AI-generated answer MUST be grounded in context retrieved from the 
student's own documents. No general-knowledge hallucination is permitted.
"""

from typing import Dict, List, Any

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.services.retrieval_service import RetrievalService
from app.services.ai_service.prompts import PromptBuilder
from app.services.ai_service.llm_client import LLMClient
from app.services.ai_service.response_parser import ResponseParser

logger = get_logger(__name__)


class AIService:
    """
    Public API for all AI-powered features.
    """

    def __init__(self, model_name: str | None = None):
        self.llm = LLMClient(model_name=model_name)

    def answer_question(
        self, 
        db: Session, 
        user_id: int, 
        query: str, 
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        RAG-powered question answering.

        1. Retrieves relevant chunks from FAISS.
        2. Builds a grounded prompt.
        3. Sends to LLM.
        4. Returns the answer with source citations.

        Args:
            db: Database session.
            user_id: The student's ID.
            query: The student's question.
            top_k: Number of context chunks to retrieve.

        Returns:
            A dict with 'answer' (str) and 'sources' (list of chunk metadata).
        """
        # 1. Retrieve context
        chunks = RetrievalService.semantic_search(db, user_id, query, top_k=top_k)
        chunk_texts = [c.text for c in chunks]

        # 2. Build prompt
        prompt = PromptBuilder.build_qa_prompt(query, chunk_texts)

        # 3. Generate answer
        raw_answer = self.llm.generate(prompt)

        # 4. Build source citations
        sources = [
            {
                "chunk_id": c.id,
                "document_id": c.document_id,
                "chunk_index": c.chunk_index,
                "text_preview": c.text[:150] + "..." if len(c.text) > 150 else c.text
            }
            for c in chunks
        ]

        logger.info(
            "Q&A completed for user %d. Retrieved %d chunks.", 
            user_id, len(chunks)
        )

        return {
            "answer": raw_answer,
            "sources": sources,
            "chunks_used": len(chunks),
        }

    def generate_quiz(
        self,
        db: Session,
        user_id: int,
        num_questions: int = 5,
        document_id: int | None = None,
        topic: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions grounded in the student's notes.

        Args:
            db: Database session.
            user_id: The student's ID.
            num_questions: How many questions to generate.
            document_id: Optional specific document to quiz on.
            topic: Optional topic string to search for context.

        Returns:
            A list of quiz question dicts with keys:
            'question', 'options', 'correct_answer', 'explanation'.
        """
        # Get context from the student's notes
        search_query = topic or "key concepts and important topics"
        chunks = RetrievalService.semantic_search(db, user_id, search_query, top_k=10)
        chunk_texts = [c.text for c in chunks]

        prompt = PromptBuilder.build_quiz_prompt(chunk_texts, num_questions)
        raw_response = self.llm.generate(prompt)

        questions = ResponseParser.parse_json_response(raw_response)
        logger.info("Generated %d quiz questions for user %d.", len(questions), user_id)

        return questions

    def generate_flashcards(
        self,
        db: Session,
        user_id: int,
        num_cards: int = 10,
        topic: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate flashcards grounded in the student's notes.

        Returns:
            A list of flashcard dicts with keys: 'front', 'back'.
        """
        search_query = topic or "key terms definitions and important concepts"
        chunks = RetrievalService.semantic_search(db, user_id, search_query, top_k=10)
        chunk_texts = [c.text for c in chunks]

        prompt = PromptBuilder.build_flashcard_prompt(chunk_texts, num_cards)
        raw_response = self.llm.generate(prompt)

        flashcards = ResponseParser.parse_json_response(raw_response)
        logger.info("Generated %d flashcards for user %d.", len(flashcards), user_id)

        return flashcards

    def generate_study_plan(
        self,
        db: Session,
        user_id: int,
        topic: str,
        num_days: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Generate a structured study plan grounded in the student's notes.

        Returns:
            A list of task dicts with keys: 'title', 'description', 'day_number'.
        """
        chunks = RetrievalService.semantic_search(db, user_id, topic, top_k=10)
        chunk_texts = [c.text for c in chunks]

        prompt = PromptBuilder.build_study_plan_prompt(topic, chunk_texts, num_days)
        raw_response = self.llm.generate(prompt)

        tasks = ResponseParser.parse_json_response(raw_response)
        logger.info("Generated %d study tasks for user %d.", len(tasks), user_id)

        return tasks
