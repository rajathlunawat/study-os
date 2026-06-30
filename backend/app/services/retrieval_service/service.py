"""
StudyOS Retrieval Service — Main Service.

Responsibility: Orchestrates vector embedding and semantic search.
Bridges the FAISS vector index with the SQLite database.
"""

from typing import List

from sqlalchemy.orm import Session

from app.core.exceptions import RAGRetrievalError
from app.db.models.document import DocumentChunk
from app.services.retrieval_service.embedder import Embedder
from app.services.retrieval_service.faiss_store import FAISSStore


class RetrievalService:
    """
    Public API for the retrieval service.
    Handles indexing new documents and performing semantic RAG searches.
    """

    @staticmethod
    def index_document_chunks(user_id: int, chunks: List[DocumentChunk]) -> None:
        """
        Takes newly parsed document chunks, generates embeddings, 
        and saves them to the user's FAISS index.
        """
        if not chunks:
            return

        texts = [chunk.text for chunk in chunks]
        chunk_ids = [chunk.id for chunk in chunks]

        # 1. Generate embeddings via sentence-transformers
        embeddings = Embedder.encode(texts)

        # 2. Add to FAISS index mapped by user_id
        store = FAISSStore(user_id=user_id)
        store.add_vectors(embeddings, chunk_ids)

    @staticmethod
    def semantic_search(db: Session, user_id: int, query: str, top_k: int = 5) -> List[DocumentChunk]:
        """
        Searches the user's FAISS index for the query and retrieves the 
        corresponding text chunks from SQLite.

        Args:
            db: SQLAlchemy database session.
            user_id: The ID of the student.
            query: The user's search query (e.g., a question).
            top_k: Number of chunks to retrieve.

        Returns:
            A list of DocumentChunk objects containing the raw text for RAG.
        """
        if not query.strip():
            return []

        try:
            # 1. Embed the query string
            query_embedding = Embedder.encode([query])

            # 2. Search FAISS for matching chunk IDs
            store = FAISSStore(user_id=user_id)
            matched_ids = store.search(query_embedding, top_k=top_k)

            if not matched_ids:
                return []

            # 3. Retrieve the actual text chunks from SQLite using the FAISS IDs
            # We use `in_` to fetch them all in a single query
            chunks = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.id.in_(matched_ids))
                .all()
            )

            # Note: SQLAlchemy's `in_` does not guarantee order. 
            # We must re-sort them based on FAISS's distance ranking (matched_ids).
            chunk_dict = {chunk.id: chunk for chunk in chunks}
            sorted_chunks = [chunk_dict[cid] for cid in matched_ids if cid in chunk_dict]

            return sorted_chunks

        except Exception as e:
            raise RAGRetrievalError(
                message="Failed to perform semantic search.",
                details={"query": query, "error": str(e)}
            ) from e
