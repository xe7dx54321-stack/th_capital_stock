CREATE TABLE IF NOT EXISTS decision_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT UNIQUE NOT NULL,
    recommendation_id TEXT NOT NULL,
    ticker TEXT,
    market TEXT,
    theme TEXT,
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    decision_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reference_price REAL,
    currency TEXT,
    suggested_position_pct REAL,
    max_position_pct REAL,
    thesis_summary TEXT,
    evidence_ids_json TEXT NOT NULL DEFAULT '[]',
    bear_case_summary TEXT,
    kill_conditions_json TEXT NOT NULL DEFAULT '[]',
    risk_notes TEXT,
    data_health_snapshot_json TEXT NOT NULL DEFAULT '{}',
    evidence_check_snapshot_json TEXT NOT NULL DEFAULT '{}',
    lint_snapshot_json TEXT NOT NULL DEFAULT '{}',
    risk_snapshot_json TEXT NOT NULL DEFAULT '{}',
    human_review_status TEXT,
    reviewer TEXT,
    review_comment TEXT,
    outcome_status TEXT NOT NULL DEFAULT 'open',
    outcome_price_1d REAL,
    outcome_price_1w REAL,
    outcome_price_1m REAL,
    outcome_price_3m REAL,
    thesis_confirmed INTEGER,
    failure_reason TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    performance_update_status TEXT,
    performance_update_reason TEXT,
    source_run_id TEXT,
    source_memory_id TEXT,
    review_due_at TEXT,
    outcome_summary TEXT,
    outcome_recorded_at TEXT,
    outcome_evidence_ids_json TEXT NOT NULL DEFAULT '[]'
);

ALTER TABLE decision_ledger ADD COLUMN source_run_id TEXT;
ALTER TABLE decision_ledger ADD COLUMN source_memory_id TEXT;
ALTER TABLE decision_ledger ADD COLUMN review_due_at TEXT;
ALTER TABLE decision_ledger ADD COLUMN outcome_summary TEXT;
ALTER TABLE decision_ledger ADD COLUMN outcome_recorded_at TEXT;
ALTER TABLE decision_ledger ADD COLUMN outcome_evidence_ids_json TEXT NOT NULL DEFAULT '[]';

CREATE INDEX IF NOT EXISTS idx_decision_ledger_ticker_time
ON decision_ledger(ticker, decision_time DESC);

CREATE INDEX IF NOT EXISTS idx_decision_ledger_review_due
ON decision_ledger(outcome_status, review_due_at);

CREATE TABLE IF NOT EXISTS decision_outcome_log (
    outcome_id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL,
    outcome_status TEXT NOT NULL CHECK (
        outcome_status IN ('open','confirmed','failed','partially_confirmed','invalidated','closed')
    ),
    summary TEXT NOT NULL,
    evidence_ids_json TEXT NOT NULL DEFAULT '[]',
    observed_price REAL,
    recorded_by TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (decision_id) REFERENCES decision_ledger(decision_id)
);

CREATE INDEX IF NOT EXISTS idx_decision_outcome_log_decision_time
ON decision_outcome_log(decision_id, recorded_at DESC);
