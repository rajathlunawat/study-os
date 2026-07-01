"""
StudyOS Backend — Complete rewrite.

Uses the NEW google-genai SDK (supports AQ. auth keys).
SQLite for persistent document storage.
Gemini 2.0 Flash for AI answers, quizzes, flashcards.
"""
import os
import re
import uuid
import traceback
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# PDF parsing
import fitz  # PyMuPDF

# ── Database ──────────────────────────────────────────────────────
from app.database import (
    save_document, get_all_documents_metadata, get_document,
    get_all_documents_text, delete_document as db_delete_document,
    get_user_stats, update_user_stats,
    save_study_task, get_all_study_tasks, update_study_task as db_update_study_task
)

from app.services.prediction_service.service import PredictionService
from app.services.planner_service.scheduler import build_schedule
from datetime import datetime, timezone

# ── Google GenAI (new SDK) ────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""
gemini_client = None

try:
    from google import genai
    from google.genai import types as genai_types
    if GEMINI_API_KEY:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print(f"✅ Gemini connected (key: {GEMINI_API_KEY[:8]}...)")
    else:
        print("⚠️  No GOOGLE_API_KEY env var — AI features disabled")
except ImportError:
    print("⚠️  google-genai package not installed — AI features disabled")

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(title="StudyOS API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ──────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    document_ids: List[str] = []

class PlanRequest(BaseModel):
    topic: str
    target_date: str
    hours_per_day: float = 2.0

class TaskUpdate(BaseModel):
    completed: bool


# ── Helpers ───────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def extract_text_from_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="replace")


def get_combined_context(doc_ids: List[str], max_chars: int = 30000) -> str:
    """Get document text. If no IDs given, use ALL documents."""
    parts = []
    total = 0

    if not doc_ids:
        docs = get_all_documents_text()
    else:
        docs = []
        for doc_id in doc_ids:
            doc = get_document(doc_id)
            if doc:
                docs.append(doc)

    for doc in docs:
        text = doc["text_content"]
        title = doc.get("title", "Untitled")
        remaining = max_chars - total
        if remaining <= 0:
            break
        chunk = text[:remaining]
        parts.append(f"--- Document: {title} ---\n{chunk}")
        total += len(chunk)

    return "\n\n".join(parts)


SYSTEM_PROMPT = """You are StudyOS, an expert AI study assistant. A student has uploaded their study documents. Your job is to help them learn effectively.

**RULES:**
1. ONLY use information from the DOCUMENT CONTENT provided below. Never make up information.
2. If the answer is not in the documents, say: "I couldn't find information about that in your uploaded documents."
3. Format ALL responses in clean Markdown with proper headings, bullet points, and structure.
4. Be thorough but concise. Use simple, clear language.

**SPECIAL COMMANDS:**
- If the student says "quiz", "/quiz", or "test me": Generate a 5-question multiple-choice quiz (A/B/C/D) based on key concepts from the document. Put the **Answer Key** at the very bottom.
- If the student says "flashcards", "/flashcards": Generate 5 flashcards formatted as:
  **Card 1**
  - **Front:** [Question or Term]
  - **Back:** [Answer or Definition]
- If the student says "summary", "summarize", or "notes": Provide a well-structured summary with headings and bullet points covering all major topics.
- If the student says "explain [topic]": Give a detailed, easy-to-understand explanation of that topic using the document content.

**FORMATTING:**
- Use ## for section headings
- Use bullet points (- ) for lists
- Use **bold** for key terms
- Use numbered lists for steps or sequences
- Add blank lines between sections for readability
"""


def call_gemini(user_message: str, context: str) -> str:
    """Call Gemini API with the new google-genai SDK."""
    if not gemini_client:
        return None

    full_prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"=== DOCUMENT CONTENT ===\n{context}\n=== END DOCUMENT CONTENT ===\n\n"
        f"Student: {user_message}"
    )

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
            config=genai_types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=2048,
            ),
        )
        return response.text
    except Exception as e:
        print(f"❌ Gemini API error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None


def format_fallback(query: str, text: str) -> str:
    """Keyword-based fallback when Gemini is unavailable."""
    query_lower = query.lower()
    words = [w for w in query_lower.split() if len(w) > 2]
    paragraphs = re.split(r'\n{2,}', text)

    scored = []
    for para in paragraphs:
        para_lower = para.lower()
        score = sum(1 for w in words if w in para_lower)
        if score > 0:
            scored.append((score, para.strip()))

    scored.sort(key=lambda x: x[0], reverse=True)

    result = []
    total = 0
    for _, para in scored[:5]:
        if total + len(para) > 2000:
            break
        # Convert bullet characters to markdown
        cleaned = re.sub(r'[•]\s*', '\n- ', para)
        cleaned = re.sub(r'(?<!\n)(\d+\.\s)', r'\n\1', cleaned)
        result.append(cleaned)
        total += len(para)

    if not result:
        # Return first chunk
        snippet = text[:2000]
        snippet = re.sub(r'[•]\s*', '\n- ', snippet)
        result = [snippet]

    body = "\n\n".join(result)

    return (
        f"## 📖 Relevant Information\n\n"
        f"*Based on your question: \"{query}\"*\n\n"
        f"{body}\n\n"
        f"---\n*⚠️ AI is not connected. For better answers, ensure GOOGLE_API_KEY is set.*"
    )


# ── Routes ────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "StudyOS Backend is running",
        "gemini": "connected" if gemini_client else "not configured",
        "documents_loaded": len(get_all_documents_metadata()),
    }


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), category: str = Form("notes")):
    file_bytes = await file.read()
    filename = file.filename or "untitled"

    if filename.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith(".txt"):
        text = extract_text_from_txt(file_bytes)
    else:
        text = extract_text_from_txt(file_bytes)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from this file.")

    doc_id = str(uuid.uuid4())
    file_type = file.content_type or "application/pdf"

    save_document(
        doc_id=doc_id,
        title=filename,
        file_type=file_type,
        status="Ready",
        uploaded_at="Just now",
        category=category,
        text_content=text
    )

    print(f"📄 Uploaded '{filename}' — {len(text)} chars extracted")

    return {
        "id": doc_id,
        "title": filename,
        "file_type": file_type,
        "status": "Ready",
        "uploaded_at": "Just now",
    }


@app.get("/api/documents")
async def get_documents():
    return get_all_documents_metadata()


@app.delete("/api/documents/{doc_id}")
async def delete_document_endpoint(doc_id: str):
    db_delete_document(doc_id)
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

    # Try Gemini first
    reply = call_gemini(req.message, context)

    # Fallback if Gemini failed
    if not reply:
        reply = format_fallback(req.message, context)

    # Return which documents were used
    sources_used = [
        doc_id for doc_id in req.document_ids
        if get_document(doc_id) is not None
    ]

    return {
        "reply": reply,
        "sources_used": sources_used,
    }

@app.get("/api/predict")
async def get_prediction():
    result = PredictionService.predict_exam_readiness(db=None, user_id=1)
    return result

@app.post("/api/planner/generate")
async def generate_planner(req: PlanRequest):
    try:
        target_date = datetime.fromisoformat(req.target_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use ISO format.")
        
    start_date = datetime.now(timezone.utc)
    topics = [t.strip() for t in req.topic.split(",")]
    tasks = build_schedule(topics, start_date, target_date, req.hours_per_day)
    
    for t in tasks:
        task_id = str(uuid.uuid4())
        save_study_task(task_id, t.title, t.description, t.scheduled_date.isoformat(), False)
        
    return {"message": f"Generated {len(tasks)} study tasks."}

@app.get("/api/planner/tasks")
async def get_tasks():
    return get_all_study_tasks()

@app.patch("/api/planner/tasks/{task_id}")
async def patch_task(task_id: str, update: TaskUpdate):
    db_update_study_task(task_id, update.completed)
    
    stats = get_user_stats()
    if stats:
        new_completion = min(stats["task_completion"] + 0.05 if update.completed else stats["task_completion"], 1.0)
        new_streak = stats["study_streak"] + 1 if update.completed else stats["study_streak"]
        update_user_stats({"task_completion": new_completion, "study_streak": new_streak})
        
    return {"status": "updated"}

@app.get("/api/stats")
async def get_stats():
    stats = get_user_stats()
    return stats or {}
