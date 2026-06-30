"""
StudyOS Document Service — Cleaner.

Responsibility: Cleans and standardizes extracted raw text.
Removes excess whitespace, non-printable characters, and fixes basic formatting
to improve RAG embedding quality.
"""

import re


class DocumentCleaner:
    """
    Provides utility methods to clean and standardize raw text strings.
    """

    @staticmethod
    def clean(text: str) -> str:
        """
        Apply a series of cleaning operations to the raw text.

        Args:
            text: The raw string extracted from a document.

        Returns:
            A cleaned and standardized string ready for chunking.
        """
        if not text:
            return ""

        text = DocumentCleaner._remove_null_bytes(text)
        text = DocumentCleaner._normalize_whitespace(text)
        text = DocumentCleaner._remove_unprintable_chars(text)
        text = text.strip()

        return text

    @staticmethod
    def _remove_null_bytes(text: str) -> str:
        """
        Remove null bytes which can crash SQLite or some embedding models.
        """
        return text.replace("\x00", "")

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """
        Convert all varied whitespace (multiple spaces, tabs, excessive newlines)
        into standard single spaces or single newlines.
        """
        # Collapse multiple spaces and tabs into a single space
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Collapse 3 or more newlines into exactly two newlines (paragraph break)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text

    @staticmethod
    def _remove_unprintable_chars(text: str) -> str:
        """
        Remove obscure control characters, keeping standard punctuation and text.
        """
        # Keeps characters from space (32) upwards, plus standard newlines and tabs
        return "".join(c for c in text if c.isprintable() or c in ("\n", "\t"))
