"""
StudyOS Utilities — Formatting.

Responsibility: Stateless utility functions for text manipulation 
and date/time standardization.
"""

from datetime import datetime, timezone
import re


def standardize_datetime(dt: datetime | None = None) -> datetime:
    """
    Ensure a datetime object is timezone-aware and set to UTC.
    If no datetime is provided, returns the current UTC time.
    
    Args:
        dt: The datetime to standardize (optional).
        
    Returns:
        A timezone-aware UTC datetime.
    """
    if dt is None:
        return datetime.now(timezone.utc)
        
    if dt.tzinfo is None:
        # If naive, assume it's UTC and make it aware
        return dt.replace(tzinfo=timezone.utc)
        
    # Convert to UTC
    return dt.astimezone(timezone.utc)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length, appending a suffix if it exceeds the limit.
    Useful for logging or UI previews without loading massive strings into memory.
    
    Args:
        text: The string to truncate.
        max_length: The maximum allowed length before truncation.
        suffix: The string to append if truncated.
        
    Returns:
        The truncated string.
    """
    if not text:
        return ""
        
    if len(text) <= max_length:
        return text
        
    # Ensure we don't truncate in the middle of a word if possible
    truncated = text[:max_length].rsplit(' ', 1)[0]
    return f"{truncated}{suffix}"


def sanitize_filename(filename: str) -> str:
    """
    Remove potentially dangerous characters from a filename.
    
    Args:
        filename: The raw filename string.
        
    Returns:
        A safe filename string containing only alphanumeric chars, dashes, and underscores.
    """
    # Replace spaces with underscores and remove non-alphanumeric chars (except dash/underscore)
    s = str(filename).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)
