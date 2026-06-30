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
    conn.commit()
    conn.close()

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
