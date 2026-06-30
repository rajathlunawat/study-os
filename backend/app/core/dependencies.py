"""
StudyOS Core — FastAPI dependency-injection helpers.

Centralised here to avoid circular imports and to give every router
a single import path for shared dependencies.
"""

from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.constants import SUPPORTED_FILE_TYPES
from app.db.session import get_db


def get_db_session(db: Session = Depends(get_db)) -> Session:
    """Typed wrapper around ``get_db`` for explicit dependency injection.

    Provides the same session but with a clearer name for router
    signatures::

        @router.get("/items")
        def list_items(db: Session = Depends(get_db_session)):
            ...
    """
    return db


def get_app_settings(
    settings: Settings = Depends(get_settings),
) -> Settings:
    """Inject the application settings as a FastAPI dependency."""
    return settings


async def validate_upload_file(
    file: UploadFile,
    settings: Settings = Depends(get_settings),
) -> UploadFile:
    """Validate an uploaded file before any processing.

    Checks:
    - File has a filename.
    - File extension is in SUPPORTED_FILE_TYPES.
    - File size does not exceed MAX_UPLOAD_SIZE_MB.

    Returns the validated ``UploadFile`` so it can be chained::

        @router.post("/upload")
        async def upload(file: UploadFile = Depends(validate_upload_file)):
            ...

    Raises:
        HTTPException 400: If any validation check fails.
    """
    # ── Filename check ───────────────────────────────────────────
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    # ── Extension check ──────────────────────────────────────────
    suffix = _extract_suffix(file.filename)
    if suffix not in SUPPORTED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type '{suffix}'. "
                f"Allowed: {', '.join(sorted(SUPPORTED_FILE_TYPES))}"
            ),
        )

    # ── Size check ───────────────────────────────────────────────
    contents = await file.read()
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File exceeds maximum size of "
                f"{settings.MAX_UPLOAD_SIZE_MB} MB."
            ),
        )

    # Reset the file pointer so downstream consumers can read again
    await file.seek(0)

    return file


def _extract_suffix(filename: str) -> str:
    """Return the lowercase file extension including the leading dot.

    Examples:
        >>> _extract_suffix("notes.PDF")
        '.pdf'
        >>> _extract_suffix("README")
        ''
    """
    dot_index = filename.rfind(".")
    if dot_index == -1:
        return ""
    return filename[dot_index:].lower()
