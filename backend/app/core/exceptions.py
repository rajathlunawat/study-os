"""
StudyOS Core — Exceptions.

Typed, hierarchical exception classes for domain-specific error handling.

Every module raises a subclass of StudyOSException rather than raw
ValueError / RuntimeError.  The global exception handler (added later in
main.py) catches the base class and returns a uniform JSON error payload.
"""

from typing import Any, Dict, Optional


class StudyOSException(Exception):
    """Base exception for all StudyOS domain errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the exception into a JSON-friendly dict."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


# ── Document errors ─────────────────────────────────────────────

class DocumentNotFoundError(StudyOSException):
    """Raised when a requested document does not exist."""

    def __init__(
        self,
        document_id: Optional[str] = None,
        message: str = "Document not found.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        _details = details or {}
        if document_id:
            _details["document_id"] = document_id
        super().__init__(message=message, details=_details)


class DocumentParsingError(StudyOSException):
    """Raised when a document cannot be parsed (corrupt PDF, etc.)."""

    def __init__(
        self,
        message: str = "Failed to parse document.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, details=details)


# ── Embedding / RAG errors ──────────────────────────────────────

class EmbeddingError(StudyOSException):
    """Raised when embedding generation fails."""

    def __init__(
        self,
        message: str = "Failed to generate embeddings.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, details=details)


class RAGRetrievalError(StudyOSException):
    """Raised when retrieval-augmented generation lookup fails."""

    def __init__(
        self,
        message: str = "RAG retrieval failed.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, details=details)


# ── Quiz / Flashcard errors ─────────────────────────────────────

class QuizGenerationError(StudyOSException):
    """Raised when quiz or flashcard generation fails."""

    def __init__(
        self,
        message: str = "Failed to generate quiz.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, details=details)


# ── Storage errors ──────────────────────────────────────────────

class StorageError(StudyOSException):
    """Raised on file-system or FAISS index I/O failures."""

    def __init__(
        self,
        message: str = "Storage operation failed.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, details=details)


# ── Validation errors ───────────────────────────────────────────

class StudyOSValidationError(StudyOSException):
    """Raised when input validation fails at the domain level.

    Named StudyOSValidationError to avoid shadowing Pydantic's
    ``ValidationError``.
    """

    def __init__(
        self,
        message: str = "Validation failed.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, details=details)


# ── Configuration errors ────────────────────────────────────────

class ConfigurationError(StudyOSException):
    """Raised when the application is misconfigured."""

    def __init__(
        self,
        message: str = "Invalid configuration.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, details=details)
