"""
StudyOS Core — Public API.

Re-exports the most commonly used objects so consuming modules can write::

    from app.core import settings, get_db, Base, StudyOSException, get_logger
"""

from app.core.config import Settings, get_settings
from app.core.constants import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MINIMUM_CHUNK_LENGTH,
    SUPPORTED_FILE_TYPES,
)
from app.core.dependencies import (
    get_app_settings,
    get_db_session,
    validate_upload_file,
)
from app.core.exceptions import (
    ConfigurationError,
    DocumentNotFoundError,
    DocumentParsingError,
    EmbeddingError,
    QuizGenerationError,
    RAGRetrievalError,
    StorageError,
    StudyOSException,
    StudyOSValidationError,
)
from app.core.logging_config import get_logger, setup_logging

# Convenience alias — the singleton settings instance
settings = get_settings()

__all__ = [
    # Config
    "Settings",
    "get_settings",
    "settings",
    # Constants
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "MINIMUM_CHUNK_LENGTH",
    "SUPPORTED_FILE_TYPES",
    # Dependencies
    "get_app_settings",
    "get_db_session",
    "validate_upload_file",
    # Exceptions
    "ConfigurationError",
    "DocumentNotFoundError",
    "DocumentParsingError",
    "EmbeddingError",
    "QuizGenerationError",
    "RAGRetrievalError",
    "StorageError",
    "StudyOSException",
    "StudyOSValidationError",
    # Logging
    "get_logger",
    "setup_logging",
]
