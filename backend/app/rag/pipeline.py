"""
StudyOS RAG — Main Pipeline.

Responsibility: Orchestrates the advanced Retrieval-Augmented Generation flow.
Instead of a naive semantic search, this pipeline introduces query 
expansion and post-retrieval reranking to ensure the LLM gets the 
highest quality context possible.
"""

from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.db.models.document import DocumentChunk
from app.services.retrieval_service import RetrievalService
# from app.rag.reranker import Reranker
# from app.rag.grounding import GroundingChecker

logger = get_logger(__name__)


class RAGPipeline:
    """
    Coordinates the advanced retrieval flow.
    """

    @staticmethod
    def retrieve_and_assemble(
        db: Session, 
        user_id: int, 
        query: str, 
        initial_k: int = 10,
        final_k: int = 5
    ) -> Dict[str, Any]:
        """
        Execute the full RAG retrieval pipeline.

        Flow:
        1. Query Expansion (Optional enhancement for future: rewrite query)
        2. Broad Retrieval: Fetch top `initial_k` chunks from FAISS.
        3. Reranking: Score the chunks against the query and keep top `final_k`.
        4. Assembly: Format chunks for the LLM.

        Args:
            db: Database session.
            user_id: The student's ID.
            query: The user's question or topic.
            initial_k: Number of chunks to retrieve from the vector database.
            final_k: Number of chunks to keep after reranking.

        Returns:
            A dictionary containing the assembled context string and the raw chunks.
        """
        logger.info("Executing RAG Pipeline for query: '%s'", query)

        # 1. Broad Retrieval (Vector Search)
        # We fetch more chunks than we need (initial_k > final_k) 
        # to cast a wide net before reranking.
        raw_chunks: List[DocumentChunk] = RetrievalService.semantic_search(
            db=db,
            user_id=user_id,
            query=query,
            top_k=initial_k,
        )

        if not raw_chunks:
            logger.warning("RAG Pipeline found no chunks for query.")
            return {
                "assembled_context": "",
                "chunks_used": []
            }

        # 2. Reranking
        # In a fully wired setup, we would call Reranker.rerank(query, raw_chunks).
        # For the scaffold, we simulate reranking by just slicing the top final_k.
        reranked_chunks = raw_chunks[:final_k]

        # 3. Assembly
        # Format the chunks into a clear, numbered block so the LLM can cite them.
        assembled_context = RAGPipeline._assemble_context(reranked_chunks)

        return {
            "assembled_context": assembled_context,
            "chunks_used": reranked_chunks
        }

    @staticmethod
    def _assemble_context(chunks: List[DocumentChunk]) -> str:
        """
        Takes a list of document chunks and formats them into a single string.
        """
        parts = []
        for i, chunk in enumerate(chunks, start=1):
            # Include metadata like chunk ID so the LLM can cite it
            parts.append(f"[Source {i} | ID: {chunk.id}]\n{chunk.text.strip()}")
            
        return "\n\n".join(parts)
