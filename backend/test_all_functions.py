"""
StudyOS — Comprehensive End-to-End Test Script.

Tests EVERY endpoint:
  1. Health Check
  2. Upload Document (TXT — the AI study material)
  3. List Documents
  4. Chat (ask about the uploaded content)
  5. Quiz (special /quiz command)
  6. Flashcards (special /flashcards command)
  7. Prediction (ML exam readiness)
  8. Stats (user progress)
  9. Planner Generate (study plan)
  10. Planner Tasks (list tasks)
  11. Planner Task Update (mark complete)
"""
import requests
import json
import time
import sys

BASE = "http://localhost:8000"
API = f"{BASE}/api"

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"

results = []

def test(name, fn):
    try:
        ok, detail = fn()
        tag = PASS if ok else FAIL
        print(f"  {tag}  {name}")
        if detail:
            # Truncate long output
            d = str(detail)
            if len(d) > 300:
                d = d[:300] + "..."
            print(f"         → {d}")
        results.append((name, ok))
    except Exception as e:
        print(f"  {FAIL}  {name}")
        print(f"         → EXCEPTION: {e}")
        results.append((name, False))


# ── Study Material ────────────────────────────────────────────────
STUDY_MATERIAL = """UNIT1: INTRODUCTION TO AI
Prof. Suyog Vinayak Pandey

Human Intelligence Vs Artificial Intelligence
For thousands of years, we have tried to understand how we think and act—that is, how our brain can perceive, understand, predict, and manipulate a world far larger and more complicated than itself.
The field of AI is concerned with not just understanding but also building intelligent entities—machines that can compute how to act effectively and safely in a wide variety of novel situations.

Human intelligence - natural smartness that people are born with.
Artificial intelligence - smartness given to machines by humans.
Humans can feel emotions like happiness, anger, and love. AI does not have real emotions, it only acts like it understands.
Humans can think in creative and new ways. AI can only do what it is trained to do.
Human intelligence is natural and emotional; AI is artificial & logical.

What is Artificial Intelligence?
Intelligence Exhibited by Machines.
Mimics cognitive functions such as Perceiving, Learning, Reasoning which are exhibited by humans.

Artificial Intelligence Systems Approaches
There are 4 classical approaches to AI systems:
1. Acting humanly (Turing Test Approach) — The acting humanly approach defines intelligence based on observable behavior. Alan Turing in 1950 through the famous Turing Test. A machine is considered intelligent if it can imitate human behavior. Criteria: Natural Language Processing (NLP), Knowledge Representation, Reasoning, Learning.
2. Thinking Humanly (Cognitive Modeling Approach) — Focuses on understanding and replicating the actual thought processes of humans. Human thinking can be studied via Introspection, Psychological experiments, Brain imaging techniques.
3. Thinking rationally (Laws of thought approach) — Based on the idea that intelligence involves correct reasoning. Originates from Aristotle's syllogisms.
4. Acting rationally (Rational Agent Approach) — Defines intelligence in terms of rational agents. A rational agent chooses actions that maximize the expected achievement of its goals.

Foundations of AI
Philosophy: Logic, reasoning.
Mathematics: Probability, optimization, logic.
Economics: Decision & Game Theory, utility.
Neuroscience: Neural Networks.
Psychology: Cognition & Learning.
Computer Engg: Hardware & Software.
Control Theory: Robotics & Systems.
Linguistics: Language & Semantics.

Applications of AI in Healthcare Sector
1. Medical Diagnostics and Imaging
2. Drug Discovery and Development
3. Remote Patient Monitoring
4. Virtual Health Assistants and Telemedicine
5. Healthcare Fraud Detection

Syllabus:
Unit-1: Introduction to Artificial Intelligence
Unit 2: Intelligent Agents
Unit 3: Problem-solving by Searching
Unit 4: Adversarial search
Unit 5: Constraint Satisfaction Problem
Unit 6: Knowledge and Reasoning
Unit 7: First-Order Logic
"""

doc_id = None  # Will be set after upload

print("\n" + "=" * 60)
print("   StudyOS — End-to-End Function Test")
print("=" * 60 + "\n")

# ── 1. Health Check ───────────────────────────────────────────────
def test_health():
    r = requests.get(f"{BASE}/health")
    data = r.json()
    ok = r.status_code == 200 and data.get("status") == "ok"
    return ok, f"status={data.get('status')}, gemini={data.get('gemini')}"

test("1. Health Check", test_health)

# ── 2. Upload Document ───────────────────────────────────────────
def test_upload():
    global doc_id
    files = {"file": ("AI_Unit1_Notes.txt", STUDY_MATERIAL.encode("utf-8"), "text/plain")}
    data = {"category": "notes"}
    r = requests.post(f"{API}/documents/upload", files=files, data=data)
    resp = r.json()
    doc_id = resp.get("id")
    ok = r.status_code == 200 and doc_id is not None
    return ok, f"doc_id={doc_id}, title={resp.get('title')}"

test("2. Upload Document", test_upload)

# ── 3. List Documents ────────────────────────────────────────────
def test_list_docs():
    r = requests.get(f"{API}/documents")
    data = r.json()
    ok = r.status_code == 200 and isinstance(data, list) and len(data) > 0
    return ok, f"Found {len(data)} document(s)"

test("3. List Documents", test_list_docs)

# ── 4. Chat — Ask about the PDF ──────────────────────────────────
def test_chat():
    payload = {
        "message": "What are the 4 approaches to AI systems?",
        "document_ids": [doc_id] if doc_id else []
    }
    r = requests.post(f"{API}/chat", json=payload, timeout=60)
    data = r.json()
    reply = data.get("reply", "")
    ok = r.status_code == 200 and len(reply) > 50
    # Check it's not hallucinating — should mention Turing or rational
    has_content = "turing" in reply.lower() or "rational" in reply.lower() or "humanly" in reply.lower()
    return ok and has_content, f"Reply length: {len(reply)} chars, mentions key terms: {has_content}"

test("4. Chat — Ask about PDF content", test_chat)

# ── 5. Quiz ──────────────────────────────────────────────────────
def test_quiz():
    payload = {
        "message": "/quiz",
        "document_ids": [doc_id] if doc_id else []
    }
    r = requests.post(f"{API}/chat", json=payload, timeout=60)
    data = r.json()
    reply = data.get("reply", "")
    ok = r.status_code == 200 and len(reply) > 100
    has_options = "A)" in reply or "A." in reply or "(A)" in reply or "a)" in reply.lower()
    return ok and has_options, f"Reply length: {len(reply)}, has MCQ options: {has_options}"

test("5. Quiz Generation (/quiz)", test_quiz)

# ── 6. Flashcards ────────────────────────────────────────────────
def test_flashcards():
    payload = {
        "message": "/flashcards",
        "document_ids": [doc_id] if doc_id else []
    }
    r = requests.post(f"{API}/chat", json=payload, timeout=60)
    data = r.json()
    reply = data.get("reply", "")
    ok = r.status_code == 200 and len(reply) > 100
    has_cards = "front" in reply.lower() or "back" in reply.lower() or "card" in reply.lower()
    return ok and has_cards, f"Reply length: {len(reply)}, has card format: {has_cards}"

test("6. Flashcard Generation (/flashcards)", test_flashcards)

# ── 7. Summary ───────────────────────────────────────────────────
def test_summary():
    payload = {
        "message": "summarize",
        "document_ids": [doc_id] if doc_id else []
    }
    r = requests.post(f"{API}/chat", json=payload, timeout=60)
    data = r.json()
    reply = data.get("reply", "")
    ok = r.status_code == 200 and len(reply) > 100
    return ok, f"Reply length: {len(reply)}"

test("7. Summary Generation", test_summary)

# ── 8. Prediction (ML) ──────────────────────────────────────────
def test_predict():
    r = requests.get(f"{API}/predict", timeout=30)
    data = r.json()
    ok = (r.status_code == 200
          and "readiness_score" in data
          and "readiness_band" in data
          and "pass_probability" in data
          and "insights" in data)
    return ok, f"score={data.get('readiness_score')}, band={data.get('readiness_band')}, backend={data.get('prediction_backend')}"

test("8. Prediction (ML Model)", test_predict)

# ── 9. User Stats ───────────────────────────────────────────────
def test_stats():
    r = requests.get(f"{API}/stats", timeout=10)
    data = r.json()
    ok = r.status_code == 200 and "quiz_accuracy" in data and "study_streak" in data
    return ok, f"accuracy={data.get('quiz_accuracy')}, streak={data.get('study_streak')}"

test("9. User Stats", test_stats)

# ── 10. Planner Generate ────────────────────────────────────────
def test_planner():
    payload = {
        "topic": "Introduction to AI, Intelligent Agents, Problem Solving by Searching",
        "target_date": "2026-07-15T00:00:00+00:00",
        "hours_per_day": 2.0
    }
    r = requests.post(f"{API}/planner/generate", json=payload, timeout=30)
    data = r.json()
    ok = r.status_code == 200 and "Generated" in data.get("message", "")
    return ok, data.get("message")

test("10. Planner — Generate Study Plan", test_planner)

# ── 11. Planner Tasks ───────────────────────────────────────────
task_id_for_update = None

def test_tasks():
    global task_id_for_update
    r = requests.get(f"{API}/planner/tasks", timeout=10)
    data = r.json()
    ok = r.status_code == 200 and isinstance(data, list) and len(data) > 0
    if ok:
        task_id_for_update = data[0].get("id")
    return ok, f"Found {len(data)} task(s)"

test("11. Planner — List Tasks", test_tasks)

# ── 12. Planner Task Update ─────────────────────────────────────
def test_task_update():
    if not task_id_for_update:
        return False, "No task ID available"
    r = requests.patch(f"{API}/planner/tasks/{task_id_for_update}",
                       json={"completed": True}, timeout=10)
    data = r.json()
    ok = r.status_code == 200 and data.get("status") == "updated"
    return ok, f"Task {task_id_for_update[:8]}... marked complete"

test("12. Planner — Update Task", test_task_update)

# ── 13. Verify Stats Updated After Task Completion ───────────────
def test_stats_updated():
    r = requests.get(f"{API}/stats", timeout=10)
    data = r.json()
    ok = r.status_code == 200 and data.get("study_streak", 0) > 0
    return ok, f"streak={data.get('study_streak')}, completion={data.get('task_completion')}"

test("13. Stats Updated After Task Completion", test_stats_updated)

# ── SUMMARY ──────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"   RESULTS: {passed}/{total} tests passed")
if passed == total:
    print("   🎉 ALL FUNCTIONS WORKING PERFECTLY!")
else:
    failed = [name for name, ok in results if not ok]
    print(f"   ⚠️  Failed: {', '.join(failed)}")
print("=" * 60 + "\n")
