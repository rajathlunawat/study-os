"""
StudyOS Schemas — Document.

Responsibility: Defines the Pydantic models for the Document entity.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ── Response Models ───────────────────────────────────────────────────────────

class DocumentChunkResponse(BaseModel):
    """
    Response schema for a specific chunk of a document.
    Usually returned as part of RAG context.
    """
    id: int
    document_id: int
    text: str
    chunk_index: int

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    """
    Response schema for a document's metadata.
    Does not include the raw chunks or file contents to keep payloads small.
    """
    id: int = Field(..., description="Unique internal database ID.")
    user_id: int = Field(..., description="ID of the user who uploaded the document.")
    filename: str = Field(..., description="Original name of the uploaded file.")
    status: str = Field(..., description="Processing status (e.g., pending, completed).")
    upload_date: datetime = Field(..., description="UTC timestamp of the upload.")
    
    # We do not expose file_path or md5_hash to the frontend for security/simplicity

    model_config = ConfigDict(from_attributes=True)
