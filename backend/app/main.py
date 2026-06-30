"""
StudyOS Main FastAPI Application Entrypoint.

This version actually parses uploaded PDFs, stores their text,
and uses Google Gemini (free tier) to answer questions grounded
in the document content — no hallucination.
"""
import os
import uuid
import tempfile
from dotenv import load_dotenv
load_dotenv()  # Load variables from .env if it exists

from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# PDF parsing
import fitz  # PyMuPDF

# Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

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

# ── Configure Gemini ──────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
gemini_model = None

if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Use gemini-1.5-flash for broad SDK compatibility
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    print(f"✅ Gemini configured with key: {GEMINI_API_KEY[:8]}...")
else:
    reason = "no google-generativeai package" if not GEMINI_AVAILABLE else "no GOOGLE_API_KEY env var"
    print(f"⚠️  Gemini not available ({reason}) — chat will use extracted text only")

# ── In-memory document store ──────────────────────────────────────
# Maps doc_id -> { metadata + extracted text }
document_store: dict = {}


class ChatRequest(BaseModel):
    message: str
    document_ids: List[str]


# ── Helpers ───────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    text_parts = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Decode plain text file."""
    return file_bytes.decode("utf-8", errors="replace")


def get_combined_context(doc_ids: List[str], max_chars: int = 30000) -> str:
    """Combine text from selected documents, truncated to fit context window."""
    parts = []
    total = 0
    for doc_id in doc_ids:
        if doc_id in document_store:
            text = document_store[doc_id]["text"]
            remaining = max_chars - total
            if remaining <= 0:
                break
            parts.append(f"--- Document: {document_store[doc_id]['title']} ---\n{text[:remaining]}")
            total += len(text[:remaining])
    return "\n\n".join(parts)


def simple_search(query: str, text: str, window: int = 1500) -> str:
    """Simple keyword search fallback — find the most relevant chunk."""
    query_lower = query.lower()
    words = query_lower.split()
    paragraphs = text.split("\n\n")

    # Score each paragraph by keyword overlap
    scored = []
    for para in paragraphs:
        para_lower = para.lower()
        score = sum(1 for w in words if w in para_lower)
        if score > 0:
            scored.append((score, para))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Return top matching paragraphs up to window size
    result = []
    total = 0
    for _, para in scored[:5]:
        if total + len(para) > window:
            break
        result.append(para.strip())
        total += len(para)

    if result:
        return "\n\n".join(result)

    # Fallback: return the first chunk of the document
    return text[:window]


# ── Routes ────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "StudyOS Backend is running",
        "gemini": "connected" if gemini_model else "not configured",
        "documents_loaded": len(document_store),
    }


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), category: str = Form("notes")):
    # Read file bytes
    file_bytes = await file.read()
    filename = file.filename or "untitled"

    # Extract text based on file type
    if filename.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith(".txt"):
        text = extract_text_from_txt(file_bytes)
    else:
        # Try as plain text
        text = extract_text_from_txt(file_bytes)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from this file.")

    doc_id = str(uuid.uuid4())
    document_store[doc_id] = {
        "id": doc_id,
        "title": filename,
        "file_type": file.content_type or "application/pdf",
        "status": "Ready",
        "uploaded_at": "Just now",
        "text": text,
        "category": category,
    }

    print(f"📄 Uploaded '{filename}' — extracted {len(text)} characters")

    return {
        "id": doc_id,
        "title": filename,
        "file_type": file.content_type or "application/pdf",
        "status": "Ready",
        "uploaded_at": "Just now",
    }


@app.get("/api/documents")
async def get_documents():
    # Return metadata only (not the full text)
    return [
        {
            "id": d["id"],
            "title": d["title"],
            "file_type": d["file_type"],
            "status": d["status"],
            "uploaded_at": d["uploaded_at"],
        }
        for d in document_store.values()
    ]


@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    if doc_id in document_store:
        del document_store[doc_id]
    return {"status": "deleted"}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    # Get document context
    context = get_combined_context(req.document_ids)

    if not context.strip():
        return {
            "reply": "Please upload a document first so I can answer questions based on your study materials.",
            "sources_used": [],
        }

    # If Gemini is available, use it for real AI answers
    if gemini_model:
        system_prompt = (
            "You are StudyOS, an AI study assistant. The student has uploaded study documents. "
            "Answer their questions ONLY using the document content provided below. "
            "If the answer is not in the documents, say so clearly. "
            "Format your answers with clear headings, bullet points, and structure. "
            "Be thorough but concise.\n\n"
            "=== DOCUMENT CONTENT ===\n"
            f"{context}\n"
            "=== END DOCUMENT CONTENT ==="
        )

        try:
            response = gemini_model.generate_content(
                f"{system_prompt}\n\nStudent question: {req.message}"
            )
            reply = response.text
        except Exception as e:
            import traceback
            print(f"❌ Gemini error: {type(e).__name__}: {e}")
            traceback.print_exc()
            # Fall back to simple search
            relevant = simple_search(req.message, context)
            reply = (
                f"## 📖 Key Points from Your Document\n\n"
                f"Based on your question: *\"{req.message}\"*\n\n"
                f"{relevant}"
            )
    else:
        # No Gemini — use keyword search to find relevant text and format it nicely
        import re
        relevant = simple_search(req.message, context)
        
        # Convert • to - and force newlines so react-markdown parses it as a real list
        formatted = re.sub(r'[•\-\*]\s+', '\n- ', relevant)
        
        # Force newlines before numbers like "1. "
        formatted = re.sub(r'\s+(\d+\.\s)', r'\n\n\1', formatted)
        
        reply = (
            f"## 📖 Key Points from Your Document\n\n"
            f"Based on your question: *\"{req.message}\"*\n\n"
            f"{formatted}"
        )

    # Return which documents were used
    sources_used = [
        doc_id for doc_id in req.document_ids
        if doc_id in document_store
    ]

    return {
        "reply": reply,
        "sources_used": sources_used,
    }
