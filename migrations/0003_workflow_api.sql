ALTER TABLE workflow_runs ADD COLUMN process_id INTEGER;
ALTER TABLE workflow_runs ADD COLUMN process_status TEXT;

CREATE TABLE IF NOT EXISTS workflow_run_requests (
    idempotency_key TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES workflow_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_workflow_run_requests_run
ON workflow_run_requests(run_id);
