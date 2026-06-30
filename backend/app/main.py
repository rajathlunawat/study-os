"""
StudyOS Main FastAPI Application Entrypoint.
"""
import uuid
import asyncio
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="StudyOS API",
    description="Backend API for the StudyOS AI Operating System for Students",
    version="1.0.0",
)

# CORS middleware for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory mock database for the UI demo ---
mock_documents = []

class ChatRequest(BaseModel):
    message: str
    document_ids: List[str]

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "StudyOS Backend is running"}

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), category: str = Form("notes")):
    # Simulate processing delay so the UI shows the loading state nicely
    await asyncio.sleep(1.5)
    
    new_doc = {
        "id": str(uuid.uuid4()),
        "title": file.filename,
        "file_type": file.content_type or "application/pdf",
        "status": "Ready",
        "uploaded_at": "Just now"
    }
    mock_documents.append(new_doc)
    return new_doc

@app.get("/api/documents")
async def get_documents():
    return mock_documents

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    global mock_documents
    mock_documents = [d for d in mock_documents if d["id"] != doc_id]
    return {"status": "deleted"}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    # Simulate AI generation delay
    await asyncio.sleep(1)
    
    # Generate a context-aware mock response based on what they uploaded
    reply = f"That is a great question about '{req.message}'. "
    sources = []
    
    if len(mock_documents) > 0:
        latest = mock_documents[-1]
        reply += f"Based on the document '{latest['title']}' you just uploaded, the core concept revolves around understanding the foundational principles outlined in the text."
        sources = [latest['id']]
    else:
        reply += "However, I notice you haven't uploaded any documents yet! Upload some study materials on the left so I can give you exact citations from your syllabus."
        
    return {
        "reply": reply,
        "sources_used": sources
    }
