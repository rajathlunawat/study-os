import sqlite3
import os
import uuid
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "studyos.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ── USERS ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    # ── SUBJECTS ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            user_id TEXT NOT NULL DEFAULT 'anonymous'
        )
    ''')

    # ── DOCUMENTS ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            title TEXT NOT NULL,
            file_type TEXT NOT NULL,
            status TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            category TEXT,
            text_content TEXT NOT NULL,
            file_url TEXT,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
        )
    ''')

    # ── USER STATS (PER SUBJECT) ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id TEXT NOT NULL UNIQUE,
            quiz_accuracy REAL DEFAULT 0.5,
            flashcard_mastery REAL DEFAULT 0.5,
            task_completion REAL DEFAULT 0.5,
            consistency_score REAL DEFAULT 0.5,
            study_streak INTEGER DEFAULT 0,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
        )
    ''')

    # ── STUDY TASKS ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_tasks (
            id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            scheduled_date TEXT NOT NULL,
            completed BOOLEAN DEFAULT 0,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
        )
    ''')

    # ── CHAT HISTORY (MEMORY) ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            role TEXT NOT NULL,  -- 'user' or 'ai'
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()


# ── USERS CRUD ──
def create_user(username: str, password_hash: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    cursor.execute('INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)', (user_id, username, password_hash, created_at))
    conn.commit()
    conn.close()
    return user_id

def get_user_by_username(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ── SUBJECT CRUD ──
def create_subject(name: str, user_id: str = "anonymous") -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    subject_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    cursor.execute('INSERT INTO subjects (id, name, created_at, user_id) VALUES (?, ?, ?, ?)', (subject_id, name, created_at, user_id))
    # Initialize stats for this subject
    cursor.execute('''
        INSERT INTO user_stats (subject_id, quiz_accuracy, flashcard_mastery, task_completion, consistency_score, study_streak)
        VALUES (?, 0.5, 0.5, 0.5, 0.5, 0)
    ''', (subject_id,))
    conn.commit()
    conn.close()
    return subject_id

def get_all_subjects(user_id: str = "anonymous"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_subject(subject_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM subjects WHERE id = ?', (subject_id,))
    conn.commit()
    conn.close()

# ── STATS ──
def get_user_stats(subject_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_stats WHERE subject_id = ?', (subject_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_user_stats(subject_id: str, updates: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [subject_id]
    cursor.execute(f'UPDATE user_stats SET {set_clause} WHERE subject_id = ?', values)
    conn.commit()
    conn.close()

# ── TASKS ──
def save_study_task(task_id: str, subject_id: str, title: str, description: str, scheduled_date: str, completed: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO study_tasks (id, subject_id, title, description, scheduled_date, completed)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (task_id, subject_id, title, description, scheduled_date, completed))
    conn.commit()
    conn.close()

def update_study_task(task_id: str, completed: bool):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE study_tasks SET completed = ? WHERE id = ?', (completed, task_id))
    
    # We need to return subject_id to update stats
    cursor.execute('SELECT subject_id FROM study_tasks WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return row["subject_id"] if row else None

def get_study_tasks(subject_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM study_tasks WHERE subject_id = ? ORDER BY scheduled_date ASC', (subject_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ── DOCUMENTS ──
def save_document(doc_id: str, subject_id: str, title: str, file_type: str, status: str, uploaded_at: str, category: str, text_content: str, file_url: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO documents (id, subject_id, title, file_type, status, uploaded_at, category, text_content, file_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (doc_id, subject_id, title, file_type, status, uploaded_at, category, text_content, file_url))
    conn.commit()
    conn.close()

def get_documents_metadata(subject_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, subject_id, title, file_type, status, uploaded_at, file_url FROM documents WHERE subject_id = ?', (subject_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_document(doc_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT title, text_content, subject_id FROM documents WHERE id = ?', (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_documents_text(subject_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, text_content FROM documents WHERE subject_id = ?', (subject_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_document(doc_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
    conn.commit()
    conn.close()

# ── CHAT HISTORY ──
def save_chat_message(subject_id: str, role: str, content: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    msg_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    cursor.execute('''
        INSERT INTO chat_history (id, subject_id, role, content, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (msg_id, subject_id, role, content, timestamp))
    conn.commit()
    conn.close()
    return msg_id

def get_chat_history(subject_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM chat_history WHERE subject_id = ? ORDER BY timestamp ASC', (subject_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Initialize on import
init_db()
