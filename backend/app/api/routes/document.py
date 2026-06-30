"""
StudyOS API — Document Routes.

Responsibility: Endpoints for uploading and listing documents.
Delegates parsing and RAG logic to DocumentService.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.core.dependencies import get_db_session, validate_upload_file
from app.schemas.document import DocumentResponse

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    user_id: int,
    file: UploadFile = Depends(validate_upload_file),
    db: Session = Depends(get_db_session)
) -> DocumentResponse:
    """
    Upload a document (PDF, TXT) for parsing and embedding.
    Processing happens asynchronously.
    """
    # TODO: Delegate to document_service.upload_and_process(db, user_id, file)
    raise HTTPException(status_code=501, detail="DocumentService not yet implemented")


@router.get("/", response_model=list[DocumentResponse])
def list_documents(
    user_id: int,
    db: Session = Depends(get_db_session)
) -> list[DocumentResponse]:
    """
    List all documents uploaded by a user.
    """
    # TODO: Delegate to document_service.get_by_user(db, user_id)
    raise HTTPException(status_code=501, detail="DocumentService not yet implemented")
