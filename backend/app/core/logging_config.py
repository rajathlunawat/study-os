"""
StudyOS Core — Logging configuration.

Structured logging using Python's stdlib ``logging`` module.

Design decision: Zero external dependencies.  The custom formatter
produces human-readable output in development and clean structured lines
in production.  It is trivially swappable for ``structlog`` later if needed.
"""

import logging
import sys
from datetime import datetime, timezone
from typing import Optional


class StudyOSFormatter(logging.Formatter):
    """Custom log formatter for StudyOS.

    Format:
        [2025-06-30T12:00:00Z] [INFO ] [app.core.config] Settings loaded
    """

    LEVEL_COLOURS: dict[str, str] = {}  # Placeholder for future colour support

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        level = record.levelname.ljust(5)
        module = record.name
        message = record.getMessage()

        formatted = f"[{timestamp}] [{level}] [{module}] {message}"

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            formatted += f"\n{record.exc_text}"

        return formatted


def setup_logging(debug: bool = False) -> None:
    """Configure the root logger for the application.

    Args:
        debug: When True, sets log level to DEBUG and enables verbose
               output.  When False, level is set to INFO.

    Should be called once at application startup before any other
    module logs.
    """
    log_level = logging.DEBUG if debug else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StudyOSFormatter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers to avoid duplicates on re-init
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if debug else logging.WARNING
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a named logger.

    Args:
        name: Logger name, typically ``__name__`` of the calling module.

    Returns:
        A ``logging.Logger`` instance scoped to *name*.

    Example::

        from app.core.logging_config import get_logger

        logger = get_logger(__name__)
        logger.info("Document uploaded", extra={"doc_id": "abc123"})
    """
    return logging.getLogger(name)
