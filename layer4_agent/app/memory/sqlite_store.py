# layer4_agent/app/memory/sqlite_store.py
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "honeypot_conversations.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            turn_number INTEGER NOT NULL,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            p_scam REAL DEFAULT 0.0,
            channel TEXT DEFAULT 'telegram'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS intelligence_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            report_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("[SQLite]: Database initialized.")

def save_turn(session_id: str, turn_number: int, sender: str, message: str, p_scam: float = 0.0, channel: str = "telegram"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversation_turns 
        (session_id, turn_number, sender, message, timestamp, p_scam, channel)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, turn_number, sender, message, datetime.now().isoformat(), p_scam, channel))
    conn.commit()
    conn.close()

def get_conversation(session_id: str) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM conversation_turns 
        WHERE session_id = ? 
        ORDER BY turn_number ASC
    """, (session_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def save_report(session_id: str, report: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO intelligence_reports (session_id, report_json, created_at)
        VALUES (?, ?, ?)
    """, (session_id, json.dumps(report), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_report(session_id: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report_json FROM intelligence_reports WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row["report_json"]) if row else None

initialize_db()