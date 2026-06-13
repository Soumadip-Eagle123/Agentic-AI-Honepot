# layer7_api_ui/api.py
import sys
import os
from typing import Optional

# Ensure imports resolve from root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Database and masking utilities
from layer4_agent.app.memory.sqlite_store import get_connection, get_conversation, get_report
from layer7_api_ui.pii_masker import PIIMasker
from layer7_api_ui import migration_manager

# Pipeline stages
from layer5_intelligence.extractor import run_extraction
from layer6_threat_intelligence.analyzer import run_layer6

app = FastAPI(
    title="Layer 7 — Secure Threat Intelligence API",
    description="Exposes threat insights to developers, SOC analysts, and law enforcement with role-based masking and audit pathways.",
    version="1.0.0"
)

# Initialize PII Masker
masker = PIIMasker()

# Models
class SimulateTurnRequest(BaseModel):
    sender: str
    message: str
    p_scam: float = 0.0
    channel: str = "telegram"

# Run migrations automatically on startup
@app.on_event("startup")
def on_startup():
    print("🚀 Running database migration on API startup...")
    migration_manager.run_migrations()

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    """Serves the main SPA Dashboard."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "status": "online",
        "message": "Layer 7 API is active. Static index.html not found yet. Write dashboard assets first."
    }

def is_system_log(message: str) -> bool:
    if not message:
        return False
    msg_lower = message.lower()
    log_indicators = [
        "📥 [layer",
        "debug [layer",
        "🔄 [layer",
        "[shorttermmemory]",
        "[conditional edge]",
        "[graph node]",
        "👑 [layer",
        "traceback (most recent call last)",
        "telegram.ext.application",
        "logging exception",
        "built packet keys:",
        "rules evaluated",
        "context dictionary generated",
        "running layer 2 ml model"
    ]
    return any(indicator in msg_lower for indicator in log_indicators)

def reconstruct_clean_timeline(session_id: str) -> dict:
    turns = get_conversation(session_id)
    clean_turns = [t for t in turns if not is_system_log(t.get("message", ""))]
    
    scammer_turns = [
        t for t in clean_turns
        if t.get("sender", "").lower() not in ["margaret", "agent", "honeypot", "margaret (honeypot)"]
    ]
    
    n = len(scammer_turns)
    hook = scammer_turns[0]["message"] if n >= 1 else None
    trust = scammer_turns[1]["message"] if n >= 2 else None
    pressure = scammer_turns[int(n * 0.6)]["message"] if n >= 3 else None
    payment = scammer_turns[-1]["message"] if n >= 4 else None
    
    return {
        "hook": hook,
        "trust_building": trust,
        "pressure": pressure,
        "payment_attempt": payment
    }

@app.get("/api/v1/sessions")
def list_sessions():
    """
    Lists all sessions present in the database, with metadata and current status.
    Provides threat levels, message counts, and timestamps.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Fetch all turns to group and filter in Python to avoid log count skew
    cursor.execute("""
        SELECT session_id, message, p_scam, timestamp 
        FROM conversation_turns
    """)
    all_turns = cursor.fetchall()
    
    from collections import defaultdict
    sessions_map = defaultdict(list)
    for row in all_turns:
        session_id = row["session_id"]
        message = row["message"]
        p_scam = row["p_scam"]
        timestamp = row["timestamp"]
        
        if not is_system_log(message):
            sessions_map[session_id].append({
                "p_scam": p_scam,
                "timestamp": timestamp
            })
            
    # Try to read session metadata if it exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_metadata'")
    has_meta_table = cursor.fetchone()
    
    sessions = []
    for session_id, turns in sessions_map.items():
        if not turns:
            continue
            
        turn_count = len(turns)
        max_p_scam = max([t["p_scam"] for t in turns])
        started_at = min([t["timestamp"] for t in turns])
        last_active_at = max([t["timestamp"] for t in turns])
        
        # Check if report exists
        cursor.execute("SELECT report_json FROM intelligence_reports WHERE session_id = ?", (session_id,))
        report_row = cursor.fetchone()
        
        region = "US-EAST"
        channel = "telegram"
        status = "finished" if report_row else "active"
        
        if has_meta_table:
            cursor.execute("SELECT region, channel, status FROM session_metadata WHERE session_id = ?", (session_id,))
            meta_row = cursor.fetchone()
            if meta_row:
                region = meta_row["region"]
                channel = meta_row["channel"]
                status = meta_row["status"]
        
        # Determine current threat details
        threat_score = 0.0
        severity = "LOW"
        
        if report_row:
            report = json_loads_safe(report_row["report_json"])
            # Run Layer 6 analyzer to get current score (cached or computed)
            try:
                l6_report = run_layer6(session_id)
                if l6_report:
                    threat_score = l6_report.get("threat_score", 0.0)
                    severity = l6_report.get("severity", "LOW")
            except Exception as e:
                # Fallback to values in the report
                threat_score = report.get("final_p_scam", 0.0) * 100.0
                severity = "HIGH" if threat_score >= 70 else "MEDIUM" if threat_score >= 40 else "LOW"
        else:
            # Fallback estimation for active session
            threat_score = max_p_scam * 100.0
            severity = "HIGH" if threat_score >= 70 else "MEDIUM" if threat_score >= 40 else "LOW"

        sessions.append({
            "session_id": session_id,
            "turn_count": turn_count,
            "max_p_scam": round(max_p_scam, 2),
            "threat_score": round(threat_score, 2),
            "severity": severity,
            "started_at": started_at,
            "last_active_at": last_active_at,
            "channel": channel,
            "region": region,
            "status": status
        })
        
    conn.close()
    
    # Sort sessions by last_active_at DESC
    sessions.sort(key=lambda s: s["last_active_at"], reverse=True)
    
    return {
        "status": "success",
        "total": len(sessions),
        "sessions": sessions
    }

@app.get("/api/v1/sessions/{session_id}/report")
def get_session_report(session_id: str, role: str = Query("soc", description="User role: dev, soc, law_enforcement")):
    """
    Retrieves the parsed threat intelligence report for the session,
    with dynamic PII masking based on the requested role.
    Runs pipeline dynamically if report is missing.
    """
    report = get_report(session_id)
    
    # Trigger pipeline on-the-fly if report is missing but conversation exists
    if not report:
        turns = get_conversation(session_id)
        if not turns:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
            
        print(f"[Layer 7 API] Report missing for {session_id}. Running extraction and analysis dynamically.")
        # Determine max p_scam for extraction (excluding logs)
        clean_turns = [t for t in turns if not is_system_log(t.get("message", ""))]
        max_p = max([t.get("p_scam", 0.0) for t in clean_turns]) if clean_turns else 0.85
        try:
            run_extraction(session_id, max_p)
            report = get_report(session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate intelligence extraction: {e}")
            
    # Retrieve Layer 6 analytics
    try:
        analytics = run_layer6(session_id)
    except Exception as e:
        print(f"[Layer 7 API] Threat analysis execution failed: {e}")
        analytics = None

    # Dynamically filter out system logs from report's raw conversation and reconstruct clean timeline
    if report:
        if "raw_conversation" in report:
            report["raw_conversation"] = [
                t for t in report["raw_conversation"]
                if not is_system_log(t.get("message", ""))
            ]
        report["timeline"] = reconstruct_clean_timeline(session_id)

    # Merge intelligence report with threat analysis
    merged_data = {
        "session_id": session_id,
        "extraction_report": report,
        "threat_analysis": analytics or {
            "threat_score": report.get("final_p_scam", 0.0) * 100.0,
            "severity": "HIGH" if report.get("scam_confirmed") else "MEDIUM",
            "campaign": {"linked_sessions": [], "shared_artifacts": []},
            "behavioral_profile": {"average_reply_gap": 0.0, "urgency_score": 0.0, "authority_score": 0.0, "question_skip_rate": 0.0},
            "llm_summary": "Automatic parsing failed. Review raw files.",
            "recommended_action": "Verify system logs manually."
        }
    }
    
    # Apply PII Redaction depending on the role
    masked_data = {
        "session_id": session_id,
        "role": role,
        "extraction_report": masker.mask_report(merged_data["extraction_report"], role),
        "threat_analysis": merged_data["threat_analysis"]
    }
    
    # Mask campaign linked details in threat analysis if needed
    if role.lower() == "soc":
        # Partially obfuscate shared artifacts
        shared_artifacts = masked_data["threat_analysis"].get("campaign", {}).get("shared_artifacts", [])
        masked_data["threat_analysis"]["campaign"]["shared_artifacts"] = [
            masker._obfuscate_value(a) for a in shared_artifacts
        ]
        
    return masked_data

@app.get("/api/v1/sessions/{session_id}/audit")
def get_session_audit(session_id: str, role: str = Query("soc", description="User role: dev, soc, law_enforcement")):
    """
    Returns turn-by-turn chat history showing scam probability ratings
    and metadata for SOC verification audit paths.
    """
    turns = get_conversation(session_id)
    if not turns:
         raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
         
    # Filter out system logs from the audit view
    clean_turns = [t for t in turns if not is_system_log(t.get("message", ""))]
    masked_turns = masker.mask_conversation(clean_turns, role)
    
    # Calculate audit metrics (scam rating changes, keyword frequencies, gaps)
    confidence_flow = []
    for i, t in enumerate(masked_turns):
        confidence_flow.append({
            "turn_number": t["turn_number"],
            "sender": t["sender"],
            "p_scam": t["p_scam"],
            "timestamp": t["timestamp"]
        })
        
    return {
        "session_id": session_id,
        "total_turns": len(clean_turns),
        "confidence_flow": confidence_flow,
        "conversation": masked_turns
    }

@app.get("/api/v1/schema-status")
def get_schema_status():
    """Returns the current database schema status and list of applied migrations."""
    try:
        applied = migration_manager.get_applied_migrations()
    except Exception as e:
        return {"status": "error", "message": f"Could not query migrations table: {e}"}
        
    # Get total file migrations
    all_migrations = []
    if os.path.exists(migration_manager.MIGRATIONS_DIR):
        for f in os.listdir(migration_manager.MIGRATIONS_DIR):
            if f.endswith(".sql"):
                all_migrations.append(f)
        all_migrations.sort()
        
    # Query details of existing tables
    conn = get_connection()
    cursor = conn.cursor()
    tables = {}
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [r["name"] for r in cursor.fetchall()]
        
        for name in table_names:
            cursor.execute(f"PRAGMA table_info({name})")
            columns = [dict(c) for c in cursor.fetchall()]
            tables[name] = columns
    except Exception as e:
        print(f"Error reading schema: {e}")
    finally:
        conn.close()
        
    return {
        "status": "success",
        "current_version": applied[-1] if applied else 0,
        "applied_migrations": applied,
        "all_available_migrations": all_migrations,
        "tables": tables
    }

@app.post("/api/v1/migrate")
def trigger_migration():
    """Runs pending database migrations."""
    try:
        migration_manager.run_migrations()
        applied = migration_manager.get_applied_migrations()
        return {
            "status": "success",
            "message": "Migrations executed successfully.",
            "current_version": applied[-1] if applied else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database migration failed: {e}")

@app.post("/api/v1/sessions/{session_id}/simulate_turn")
def simulate_conversation_turn(session_id: str, request: SimulateTurnRequest):
    """
    Mock endpoint to insert conversation turns into SQLite.
    Simplifies developer testing of the boundary without running the Telegram Bot.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Fetch current max turn_number
    cursor.execute("SELECT MAX(turn_number) as max_turn FROM conversation_turns WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    next_turn = (row["max_turn"] + 1) if (row and row["max_turn"] is not None) else 1
    
    conn.close()
    
    # 2. Save turn
    from layer4_agent.app.memory.sqlite_store import save_turn
    save_turn(
        session_id=session_id,
        turn_number=next_turn,
        sender=request.sender,
        message=request.message,
        p_scam=request.p_scam,
        channel=request.channel
    )
    
    # 3. Save mock session metadata if table exists
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_metadata'")
    if cursor.fetchone():
        from datetime import datetime
        cursor.execute("""
            INSERT INTO session_metadata (session_id, channel, region, started_at, status)
            VALUES (?, ?, ?, ?, 'active')
            ON CONFLICT(session_id) DO UPDATE SET status = 'active'
        """, (session_id, request.channel, "US-WEST", datetime.now().isoformat()))
        conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "session_id": session_id,
        "turn_inserted": next_turn,
        "sender": request.sender
    }

@app.post("/api/v1/sessions/{session_id}/run_analysis")
def force_pipeline_run(session_id: str):
    """Trigger the full extraction and analytics pipeline (Layer 5 + 6) for a session."""
    turns = get_conversation(session_id)
    if not turns:
        raise HTTPException(status_code=404, detail="No conversation records found.")
        
    max_p = max([t.get("p_scam", 0.0) for t in turns])
    
    try:
        print(f"[Layer 7 API] Explicit pipeline run for {session_id} started.")
        # Trigger Extractor
        run_extraction(session_id, max_p)
        # Trigger Analyzer
        result = run_layer6(session_id)
        
        # Update session status to finished in metadata if table exists
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_metadata'")
        if cursor.fetchone():
            cursor.execute("UPDATE session_metadata SET status = 'finished' WHERE session_id = ?", (session_id,))
            conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": "L5 Extractor & L6 Analyzer pipelines completed successfully.",
            "threat_analysis": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {e}")

# Helpers
import json
def json_loads_safe(data):
    try:
        return json.loads(data)
    except:
        return {}
