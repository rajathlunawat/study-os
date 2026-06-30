"""
StudyOS Document Service — Chunker.

Responsibility: Splits cleaned text into overlapping segments.
Ensures chunks are roughly uniform in size, making them ideal for
sentence-transformer embeddings.
"""

from app.core.config import get_settings

settings = get_settings()


class DocumentChunker:
    """
    Handles splitting large texts into smaller, overlapping chunks.
    Uses a naive character/word-based approach for zero-dependency simplicity.
    (For production NLP, a tokenizer like tiktoken could be swapped in here).
    """

    @staticmethod
    def chunk_text(
        text: str, 
        chunk_size: int = settings.CHUNK_SIZE, 
        chunk_overlap: int = settings.CHUNK_OVERLAP
    ) -> list[str]:
        """
        Split text into overlapping chunks.
        
        This implementation splits by words (whitespace) to avoid slicing 
        words in half, then groups them approximately by token count 
        (assuming ~1 word = 1.3 tokens loosely).

        Args:
            text: The cleaned document text.
            chunk_size: Target maximum words/tokens per chunk.
            chunk_overlap: Number of words/tokens to overlap between chunks.

        Returns:
            A list of text chunk strings.
        """
        if not text:
            return []

        # Simple whitespace tokenization
        words = text.split()
        
        if not words:
            return []
            
        if len(words) <= chunk_size:
            return [" ".join(words)]

        chunks = []
        start_idx = 0
        total_words = len(words)

        while start_idx < total_words:
            # Calculate the end index for the current chunk
            end_idx = min(start_idx + chunk_size, total_words)
            
            # Slice the words and join them back into a string
            chunk_words = words[start_idx:end_idx]
            chunks.append(" ".join(chunk_words))
            
            # Move the start pointer forward, stepping back by the overlap amount
            # If start_idx doesn't advance (e.g. overlap >= chunk_size), force it forward
            step = max(chunk_size - chunk_overlap, 1)
            start_idx += step

        return chunks
