"""
StudyOS DB — Declarative Base.

Defines the SQLAlchemy Base class.
Table names are explicitly defined in each model to avoid
complex automatic pluralization rules, keeping things explicit.
"""

from typing import Any
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all StudyOS ORM models."""

    id: Any
    __name__: str
