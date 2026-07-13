ALTER TABLE risk_alert ADD COLUMN fingerprint TEXT;
ALTER TABLE risk_alert ADD COLUMN source_state TEXT;
ALTER TABLE risk_alert ADD COLUMN lifecycle_status TEXT NOT NULL DEFAULT 'opened';
ALTER TABLE risk_alert ADD COLUMN first_seen_at TEXT;
ALTER TABLE risk_alert ADD COLUMN last_seen_at TEXT;
ALTER TABLE risk_alert ADD COLUMN occurrence_count INTEGER NOT NULL DEFAULT 1;
ALTER TABLE risk_alert ADD COLUMN resolved_at TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_risk_alert_fingerprint
ON risk_alert(fingerprint)
WHERE fingerprint IS NOT NULL;
