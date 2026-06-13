-- Migration 002: Add Risk level, Scam type, Threat score, and Indices
-- Note: SQLite doesn't support IF NOT EXISTS in ALTER TABLE ADD COLUMN.
-- These will be run safely by checking table info in our python migration manager.
ALTER TABLE intelligence_reports ADD COLUMN scam_type TEXT DEFAULT 'unknown';
ALTER TABLE intelligence_reports ADD COLUMN risk_level TEXT DEFAULT 'LOW';
ALTER TABLE intelligence_reports ADD COLUMN threat_score REAL DEFAULT 0.0;

-- Indices for performance optimization
CREATE INDEX IF NOT EXISTS idx_turns_session_p_scam ON conversation_turns(session_id, p_scam);
CREATE INDEX IF NOT EXISTS idx_reports_session_id ON intelligence_reports(session_id);
