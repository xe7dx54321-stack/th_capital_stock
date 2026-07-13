CREATE TABLE IF NOT EXISTS workflow_runs (
    run_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('queued','running','waiting_review','completed','failed','cancelled')
    ),
    input_json TEXT NOT NULL DEFAULT '{}',
    summary_json TEXT NOT NULL DEFAULT '{}',
    error_code TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    cancel_requested_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_status_created
ON workflow_runs(status, created_at DESC);

CREATE TABLE IF NOT EXISTS workflow_events (
    run_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    stage_id TEXT,
    level TEXT NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, sequence),
    FOREIGN KEY (run_id) REFERENCES workflow_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_workflow_events_run_created
ON workflow_events(run_id, created_at);

CREATE TABLE IF NOT EXISTS workflow_artifacts (
    artifact_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    title TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES workflow_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_workflow_artifacts_run_created
ON workflow_artifacts(run_id, created_at);

CREATE TABLE IF NOT EXISTS memory_items (
    memory_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('candidate','approved','rejected','archived')
    ),
    confidence REAL,
    source_run_id TEXT,
    valid_from TEXT,
    valid_until TEXT,
    last_verified_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_evidence_links (
    memory_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    relation TEXT NOT NULL CHECK (
        relation IN ('supports','contradicts','supersedes','context')
    ),
    created_at TEXT NOT NULL,
    PRIMARY KEY (memory_id, evidence_id, relation)
);
