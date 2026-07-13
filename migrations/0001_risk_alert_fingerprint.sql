CREATE TABLE IF NOT EXISTS risk_alert (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_time TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    ts_code TEXT,
    message TEXT,
    action TEXT,
    acknowledged INTEGER DEFAULT 0
);

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
