"""
StudyOS Document Service — Main Service.

Responsibility: Orchestrates the document upload lifecycle.
Coordinates saving the file, parsing, cleaning, chunking, and database insertion.
"""

import hashlib
import shutil
from pathlib import Path
from typing import List

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import StorageError
from app.db.models.document import Document, DocumentChunk
from app.services.document_service.parser import DocumentParser
from app.services.document_service.cleaner import DocumentCleaner
from app.services.document_service.chunker import DocumentChunker

settings = get_settings()

# Ensure a local directory exists for storing uploaded files
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class DocumentService:
    """
    Public API for document operations.
    """

    @staticmethod
    def upload_and_process(db: Session, user_id: int, file: UploadFile) -> Document:
        """
        Full pipeline: Save to disk, parse, clean, chunk, and save to SQLite.
        
        Note: In a high-traffic production system, parsing and chunking 
        should be offloaded to a background task (e.g., Celery). For StudyOS 
        (local usage), inline synchronous execution is acceptable.
        """
        # 1. Read file bytes and calculate MD5
        file_bytes = file.file.read()
        md5_hash = hashlib.md5(file_bytes).hexdigest()
        
        # Reset file pointer for saving
        file.file.seek(0)
        
        # 2. Save file to disk safely
        safe_filename = f"{md5_hash}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise StorageError("Failed to save uploaded file to disk.") from e

        # 3. Create initial DB record (Status: processing)
        db_doc = Document(
            user_id=user_id,
            filename=file.filename,
            file_path=str(file_path),
            status="processing",
            md5_hash=md5_hash
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        try:
            # 4. Extract, Clean, and Chunk
            raw_text = DocumentParser.extract_text(file_path)
            cleaned_text = DocumentCleaner.clean(raw_text)
            chunks = DocumentChunker.chunk_text(cleaned_text)

            # 5. Save chunks to SQLite
            db_chunks = []
            for idx, chunk_text in enumerate(chunks):
                db_chunks.append(
                    DocumentChunk(
                        document_id=db_doc.id,
                        text=chunk_text,
                        chunk_index=idx
                    )
                )
            
            db.add_all(db_chunks)
            db_doc.status = "completed"
            db.commit()
            db.refresh(db_doc)
            
        except Exception:
            # If parsing or chunking fails, mark the document as error
            db_doc.status = "error"
            db.commit()
            raise

        return db_doc

    @staticmethod
    def get_by_user(db: Session, user_id: int) -> List[Document]:
        """
        Retrieve all documents belonging to a user.
        """
        return db.query(Document).filter(Document.user_id == user_id).all()
