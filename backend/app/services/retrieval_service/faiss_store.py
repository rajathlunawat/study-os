"""
StudyOS Retrieval Service — FAISS Store.

Responsibility: Manages the local FAISS vector index.
Handles index creation, saving to disk, and ID mapping.

Design Decision: We use `faiss.IndexIDMap` wrapped around `faiss.IndexFlatL2`.
This allows us to explicitly assign our SQLite DocumentChunk.id as the FAISS ID,
making retrieval lookups trivial.
"""

import json
from pathlib import Path
from typing import List
import numpy as np
import faiss

from app.core.config import get_settings
from app.core.exceptions import StorageError

_settings = get_settings()

class FAISSStore:
    """
    Encapsulates FAISS index operations for a specific user.
    To ensure data isolation, each user gets their own FAISS index file.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.index_dir = _settings.faiss_index_path
        self.index_path = self.index_dir / f"user_{user_id}.index"
        
        # Ensure the directory exists
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.index = self._load_or_create_index()

    def _load_or_create_index(self) -> faiss.IndexIDMap:
        """
        Loads the user's FAISS index from disk if it exists.
        Otherwise, creates a new empty L2 index wrapped in an IDMap.
        """
        if self.index_path.exists():
            try:
                return faiss.read_index(str(self.index_path))
            except Exception as e:
                # If the index is corrupt, we'll raise an error.
                # A robust production system might automatically rebuild it from SQLite.
                raise StorageError(
                    f"Failed to load FAISS index for user {self.user_id}", 
                    details={"error": str(e)}
                ) from e
        
        # Create a new index: 
        # IndexFlatL2 is exact search (no approximation), fine for thousands of chunks.
        base_index = faiss.IndexFlatL2(_settings.EMBEDDING_DIMENSION)
        # Wrap it in an IDMap so we can supply our own IDs (instead of sequential 0, 1, 2...)
        return faiss.IndexIDMap(base_index)

    def save(self) -> None:
        """
        Write the current state of the index to disk.
        """
        try:
            faiss.write_index(self.index, str(self.index_path))
        except Exception as e:
            raise StorageError(
                f"Failed to save FAISS index for user {self.user_id}", 
                details={"error": str(e)}
            ) from e

    def add_vectors(self, embeddings: np.ndarray, chunk_ids: List[int]) -> None:
        """
        Add a batch of dense vectors and their corresponding SQLite IDs to the index.
        """
        if len(embeddings) != len(chunk_ids):
            raise ValueError("Number of embeddings must match number of chunk_ids.")
            
        if len(embeddings) == 0:
            return

        # FAISS requires IDs to be 64-bit integers
        ids_array = np.array(chunk_ids, dtype=np.int64)
        
        # FAISS requires vectors to be 32-bit floats
        embeddings_array = np.array(embeddings, dtype=np.float32)

        self.index.add_with_ids(embeddings_array, ids_array)
        self.save()

    def search(self, query_embedding: np.ndarray, top_k: int = _settings.TOP_K_RESULTS) -> List[int]:
        """
        Search the index for the top_k vectors closest to the query.

        Args:
            query_embedding: A single vector (shape: 1 x DIM) representing the search query.
            top_k: The number of closest matches to return.

        Returns:
            A list of chunk_ids (SQLite primary keys) matching the query.
        """
        if self.index.ntotal == 0:
            return []

        query_array = np.array(query_embedding, dtype=np.float32)
        
        # Ensure it's a 2D array (1, DIM)
        if len(query_array.shape) == 1:
            query_array = np.expand_dims(query_array, axis=0)

        # D contains distances, I contains the corresponding chunk_ids
        D, I = self.index.search(query_array, top_k)
        
        # I[0] gives the IDs for the first (and only) query vector
        # Filter out -1, which FAISS returns if it can't find enough matches
        return [int(chunk_id) for chunk_id in I[0] if chunk_id != -1]
