import sqlite3
import json
from typing import List, Optional, Dict, Any
from config import DB_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Cases table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_number TEXT UNIQUE NOT NULL,
        litigant_name TEXT NOT NULL,
        relative_name TEXT,
        relative_contact TEXT,
        language TEXT DEFAULT 'mr-IN',
        court_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Order sheets table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_sheets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_number TEXT NOT NULL,
        hearing_date TEXT NOT NULL,
        next_date TEXT NOT NULL,
        stage TEXT,
        order_summary TEXT,
        action_required TEXT,
        documents_json TEXT,
        confidence_score REAL DEFAULT 0.95,
        raw_text TEXT,
        image_path TEXT,
        audio_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (case_number) REFERENCES cases (case_number)
    );
    """)
    
    # Lawyer voice updates
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lawyer_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_number TEXT NOT NULL,
        audio_path TEXT,
        transcript TEXT,
        claimed_stage TEXT,
        claimed_action TEXT,
        claimed_next_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (case_number) REFERENCES cases (case_number)
    );
    """)
    
    # Mismatch reports
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mismatches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_number TEXT NOT NULL,
        hearing_date TEXT,
        has_mismatch INTEGER DEFAULT 0,
        severity TEXT,
        summary_en TEXT,
        summary_mr TEXT,
        court_claim TEXT,
        lawyer_claim TEXT,
        questions_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (case_number) REFERENCES cases (case_number)
    );
    """)
    
    # Case diary
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS diary_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_number TEXT NOT NULL,
        entry_date TEXT NOT NULL,
        title_en TEXT,
        title_mr TEXT,
        summary_mr TEXT,
        audio_path TEXT,
        has_mismatch INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (case_number) REFERENCES cases (case_number)
    );
    """)
    
    conn.commit()
    conn.close()

def save_case(case_number: str, litigant_name: str, court_name: str, language: str = "mr-IN", relative_name: str = "Sagar Patil (Son)", relative_contact: str = "+91 98765 43210"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO cases (case_number, litigant_name, relative_name, relative_contact, language, court_name)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (case_number, litigant_name, relative_name, relative_contact, language, court_name))
    conn.commit()
    conn.close()

def save_order_sheet(case_number: str, hearing_date: str, next_date: str, stage: str,
                     order_summary: str, action_required: str, documents: List[str],
                     confidence: float, raw_text: str = "", image_path: str = "", audio_path: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO order_sheets (case_number, hearing_date, next_date, stage, order_summary, action_required, documents_json, confidence_score, raw_text, image_path, audio_path)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (case_number, hearing_date, next_date, stage, order_summary, action_required, json.dumps(documents, ensure_ascii=False), confidence, raw_text, image_path, audio_path))
    sheet_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sheet_id

def save_lawyer_note(case_number: str, audio_path: str, transcript: str, claimed_stage: str, claimed_action: str, claimed_next_date: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO lawyer_notes (case_number, audio_path, transcript, claimed_stage, claimed_action, claimed_next_date)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (case_number, audio_path, transcript, claimed_stage, claimed_action, claimed_next_date))
    note_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return note_id

def save_mismatch(case_number: str, hearing_date: str, has_mismatch: bool, severity: str,
                  summary_en: str, summary_mr: str, court_claim: str, lawyer_claim: str, questions: List[str]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO mismatches (case_number, hearing_date, has_mismatch, severity, summary_en, summary_mr, court_claim, lawyer_claim, questions_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (case_number, hearing_date, 1 if has_mismatch else 0, severity, summary_en, summary_mr, court_claim, lawyer_claim, json.dumps(questions, ensure_ascii=False)))
    m_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return m_id

def save_diary_entry(case_number: str, entry_date: str, title_en: str, title_mr: str, summary_mr: str, audio_path: str = "", has_mismatch: bool = False) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO diary_entries (case_number, entry_date, title_en, title_mr, summary_mr, audio_path, has_mismatch)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (case_number, entry_date, title_en, title_mr, summary_mr, audio_path, 1 if has_mismatch else 0))
    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return entry_id

def get_diary(case_number: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM diary_entries WHERE case_number = ? ORDER BY id DESC", (case_number,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_latest_order(case_number: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM order_sheets WHERE case_number = ? ORDER BY id DESC LIMIT 1", (case_number,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# Initialize tables upon module import
init_db()
