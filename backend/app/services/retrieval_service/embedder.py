"""
StudyOS Retrieval Service — Embedder.

Responsibility: Handles turning text strings into vector embeddings using 
the sentence-transformers library.

Design Decision: The embedding model is loaded as a lazy singleton. 
This is crucial for an 8GB RAM laptop, ensuring the model is only loaded 
once and kept in memory across requests.
"""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.exceptions import EmbeddingError

_settings = get_settings()

class Embedder:
    """
    Singleton wrapper for the sentence-transformer model.
    """
    _instance: SentenceTransformer | None = None

    @classmethod
    def _get_model(cls) -> SentenceTransformer:
        """
        Lazy-loads the embedding model.
        """
        if cls._instance is None:
            try:
                # all-MiniLM-L6-v2 is fast, small (under 100MB RAM), 
                # and maps text to a 384-dimensional dense vector space.
                cls._instance = SentenceTransformer(_settings.EMBEDDING_MODEL)
            except Exception as e:
                raise EmbeddingError(
                    message=f"Failed to load embedding model: {_settings.EMBEDDING_MODEL}",
                    details={"error": str(e)}
                ) from e
        return cls._instance

    @classmethod
    def encode(cls, text: Union[str, List[str]]) -> np.ndarray:
        """
        Convert text(s) into dense vector embeddings.

        Args:
            text: A single string or a list of strings to embed.

        Returns:
            A numpy array of shape (N, 384) representing the embeddings.
        
        Raises:
            EmbeddingError: If the encoding process fails.
        """
        model = cls._get_model()
        try:
            # show_progress_bar is disabled to avoid stdout spam in logs
            embeddings = model.encode(
                text, 
                show_progress_bar=False, 
                convert_to_numpy=True
            )
            return embeddings
        except Exception as e:
            raise EmbeddingError(
                message="Failed to encode text to vectors.",
                details={"error": str(e)}
            ) from e
