-- Migration 003: Create Session Metadata Table for campaigns tracking
CREATE TABLE IF NOT EXISTS session_metadata (
    session_id TEXT PRIMARY KEY,
    channel TEXT DEFAULT 'telegram',
    region TEXT DEFAULT 'US-EAST',
    scammer_ip TEXT,
    started_at TEXT NOT NULL,
    status TEXT DEFAULT 'active'
);

CREATE INDEX IF NOT EXISTS idx_metadata_session_id ON session_metadata(session_id);
