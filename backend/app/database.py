import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "studyos.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create the documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            file_type TEXT NOT NULL,
            status TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            category TEXT,
            text_content TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_accuracy REAL DEFAULT 0.5,
            flashcard_mastery REAL DEFAULT 0.5,
            task_completion REAL DEFAULT 0.5,
            consistency_score REAL DEFAULT 0.5,
            study_streak INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            scheduled_date TEXT NOT NULL,
            completed BOOLEAN DEFAULT 0
        )
    ''')
    
    # Initialize default user stats if not exists
    cursor.execute('SELECT COUNT(*) FROM user_stats')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO user_stats (quiz_accuracy, flashcard_mastery, task_completion, consistency_score, study_streak)
            VALUES (0.5, 0.5, 0.5, 0.5, 0)
        ''')
        
    conn.commit()
    conn.close()

def get_user_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_stats LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_user_stats(updates: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values())
    cursor.execute(f'UPDATE user_stats SET {set_clause} WHERE id = 1', values)
    conn.commit()
    conn.close()
    
def save_study_task(task_id, title, description, scheduled_date, completed=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO study_tasks (id, title, description, scheduled_date, completed)
        VALUES (?, ?, ?, ?, ?)
    ''', (task_id, title, description, scheduled_date, completed))
    conn.commit()
    conn.close()

def update_study_task(task_id, completed):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE study_tasks SET completed = ? WHERE id = ?', (completed, task_id))
    conn.commit()
    conn.close()

def get_all_study_tasks():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM study_tasks ORDER BY scheduled_date ASC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_document(doc_id, title, file_type, status, uploaded_at, category, text_content):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO documents (id, title, file_type, status, uploaded_at, category, text_content)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (doc_id, title, file_type, status, uploaded_at, category, text_content))
    conn.commit()
    conn.close()

def get_all_documents_metadata():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, file_type, status, uploaded_at FROM documents')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_document(doc_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT title, text_content FROM documents WHERE id = ?', (doc_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_all_documents_text():
    """Fallback if no document IDs are provided."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, text_content FROM documents')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_document(doc_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
    conn.commit()
    conn.close()

# Initialize the database on import
init_db()
