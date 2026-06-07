# layer5_intelligence/api.py
import sys
import os

# Make sure imports work from root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from layer4_agent.app.memory.sqlite_store import get_conversation, get_report
from layer5_intelligence.extractor import run_extraction

app = FastAPI(
    title="Layer 5 — Scam Intelligence API",
    description="Extracts structured intelligence from honeypot conversations",
    version="1.0.0"
)


# ─── Request Models ───────────────────────────────────────────────────────────

class ExtractionRequest(BaseModel):
    session_id: str
    final_p_scam: Optional[float] = 0.85


class ManualTurnRequest(BaseModel):
    session_id: str
    sender: str
    message: str
    p_scam: Optional[float] = 0.0
    channel: Optional[str] = "telegram"


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "layer": 5,
        "name": "Intelligence Extractor",
        "status": "online",
        "version": "1.0.0"
    }


@app.post("/extract")
def extract_intelligence(request: ExtractionRequest):
    """
    Triggers intelligence extraction for a session.
    Reads conversation from SQLite, runs extractor, returns JSON report.
    """
    conversation = get_conversation(request.session_id)

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=f"No conversation found for session_id: {request.session_id}"
        )

    report = run_extraction(request.session_id, request.final_p_scam)

    if not report:
        raise HTTPException(
            status_code=500,
            detail="Extraction failed. Check logs."
        )

    return {
        "status": "success",
        "session_id": request.session_id,
        "report": report
    }


@app.get("/intel/{session_id}")
def get_intelligence(session_id: str):
    """
    Returns the saved intelligence report for a session.
    This is what Layer 6 (Arista) calls.
    """
    report = get_report(session_id)

    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for session_id: {session_id}"
        )

    return {
        "status": "success",
        "session_id": session_id,
        "report": report
    }


@app.get("/conversation/{session_id}")
def get_raw_conversation(session_id: str):
    """
    Returns raw conversation turns for a session.
    Useful for debugging and Layer 6 audit trails.
    """
    conversation = get_conversation(session_id)

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=f"No conversation found for session_id: {session_id}"
        )

    return {
        "status": "success",
        "session_id": session_id,
        "turn_count": len(conversation),
        "conversation": conversation
    }


@app.post("/manual_turn")
def add_manual_turn(request: ManualTurnRequest):
    """
    Manually add a conversation turn to the database.
    Useful for testing without running the full Telegram bot.
    """
    from layer4_agent.app.memory.sqlite_store import save_turn
    save_turn(
        session_id=request.session_id,
        turn_number=1,
        sender=request.sender,
        message=request.message,
        p_scam=request.p_scam,
        channel=request.channel
    )
    return {
        "status": "saved",
        "session_id": request.session_id,
        "sender": request.sender,
        "message": request.message
    }


@app.get("/sessions")
def list_sessions():
    """
    Lists all session IDs that have intelligence reports.
    """
    from layer4_agent.app.memory.sqlite_store import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT session_id FROM intelligence_reports")
    sessions = [row["session_id"] for row in cursor.fetchall()]
    conn.close()
    return {
        "status": "success",
        "total": len(sessions),
        "sessions": sessions
    }