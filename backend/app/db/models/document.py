"""
StudyOS DB Models — Document.

Responsibility: Defines the SQLAlchemy ORM models for the `document` 
and `document_chunk` tables.
Contains no business logic, only the schema definition and relationships.
"""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Document(Base):
    """
    Represents an uploaded file (e.g., PDF lecture notes, syllabus).
    
    Attributes:
        id: Primary key.
        user_id: Foreign key linking the document to its owner.
        filename: Original name of the uploaded file.
        file_path: Absolute or relative path to the stored file on disk.
        status: Processing state (e.g., 'pending', 'processing', 'completed').
        upload_date: Timestamp of the file upload (UTC).
        md5_hash: Hash of the file to prevent duplicate uploads.
    """
    __tablename__ = "document"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, nullable=False)
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    md5_hash: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    
    user: Mapped["User"] = relationship("User", back_populates="documents")
    
    # A document is parsed into many chunks for RAG vector search
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )
    
    # A document can have quizzes generated from it
    quizzes: Mapped[list["Quiz"]] = relationship(
        "Quiz", back_populates="document"
    )
    
    # A document can have flashcards generated from it
    flashcards: Mapped[list["Flashcard"]] = relationship(
        "Flashcard", back_populates="document"
    )


class DocumentChunk(Base):
    """
    Represents a specific parsed chunk of text from a Document.
    While vectors are stored in FAISS, the raw text is stored here.
    
    Attributes:
        id: Primary key.
        document_id: Foreign key linking to the parent Document.
        text: The raw text extracted from the document.
        chunk_index: The sequential order of this chunk in the document.
    """
    __tablename__ = "document_chunk"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"), index=True, nullable=False)
    
    text: Mapped[str] = mapped_column(nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # ── Relationships ─────────────────────────────────────────────────────────
    
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
