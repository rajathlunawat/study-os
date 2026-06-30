"""
StudyOS RAG — Reranker.

Responsibility: Re-orders a list of retrieved chunks to ensure the most 
relevant ones are at the top.

Design Decision: Pure vector search (FAISS) is fast but sometimes returns 
chunks that share words with the query but don't answer it. A reranker 
fixes this. Since we need low RAM usage (8GB laptop), we avoid heavy 
Cross-Encoder models. Instead, we use a lightweight keyword-overlap heuristic
(a simplified BM25 approach) to boost chunks that contain exact query keywords.
"""

from typing import List
from collections import Counter
import re

from app.db.models.document import DocumentChunk


class Reranker:
    """
    Lightweight heuristic reranker for retrieved document chunks.
    """

    @staticmethod
    def rerank(query: str, chunks: List[DocumentChunk], top_k: int = 5) -> List[DocumentChunk]:
        """
        Sorts the provided chunks based on a combination of their original 
        vector search order and exact keyword overlap.

        Args:
            query: The user's search query.
            chunks: The raw chunks retrieved from FAISS (ordered by vector distance).
            top_k: How many chunks to return after reranking.

        Returns:
            A new list of DocumentChunks, sorted by the reranking score.
        """
        if not chunks:
            return []

        # 1. Clean and tokenize the query into significant keywords
        # Remove common stop words for better overlap scoring
        stop_words = {"what", "is", "the", "a", "an", "how", "why", "in", "of", "and", "to"}
        query_words = set(re.findall(r'\w+', query.lower()))
        keywords = query_words - stop_words

        if not keywords:
            # If query was only stop words, just return the FAISS ranking
            return chunks[:top_k]

        scored_chunks = []
        for index, chunk in enumerate(chunks):
            # 2. Base score derived from FAISS rank. 
            # (Chunks earlier in the list get a higher base score).
            # Max base score is len(chunks), decreasing by 1 for each subsequent chunk.
            base_score = len(chunks) - index

            # 3. Calculate Keyword Overlap (simplified BM25)
            chunk_text_lower = chunk.text.lower()
            overlap_count = sum(1 for kw in keywords if kw in chunk_text_lower)
            
            # Boost score heavily based on exact keyword matches
            boost_score = overlap_count * 2.0 

            final_score = base_score + boost_score
            scored_chunks.append((final_score, chunk))

        # 4. Sort by final score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        # 5. Extract and return the top_k chunks
        reranked = [item[1] for item in scored_chunks]
        return reranked[:top_k]
