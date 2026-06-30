"""
StudyOS Core — Constants.

Immutable, application-wide constants that are NOT user-configurable.
For user-configurable values, see config.py.
"""

from typing import FrozenSet


# ── Supported file types for upload ──────────────────────────────
SUPPORTED_FILE_TYPES: FrozenSet[str] = frozenset({".pdf", ".txt", ".md"})

# ── File system limits ───────────────────────────────────────────
MAX_FILENAME_LENGTH: int = 255

# ── Pagination ───────────────────────────────────────────────────
DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100

# ── Document processing guards ───────────────────────────────────
MINIMUM_CHUNK_LENGTH: int = 50

# ── HTTP status descriptions (for consistent error payloads) ─────
ERROR_TYPE_VALIDATION: str = "validation_error"
ERROR_TYPE_NOT_FOUND: str = "not_found"
ERROR_TYPE_PROCESSING: str = "processing_error"
ERROR_TYPE_INTERNAL: str = "internal_error"
