ALTER TABLE memory_items ADD COLUMN parent_memory_id TEXT;
ALTER TABLE memory_items ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE memory_items ADD COLUMN field_diff_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE memory_items ADD COLUMN reviewed_by TEXT;
ALTER TABLE memory_items ADD COLUMN review_reason TEXT;
ALTER TABLE memory_items ADD COLUMN reviewed_at TEXT;

CREATE INDEX IF NOT EXISTS idx_memory_entity_status_version
ON memory_items(entity_type, entity_id, memory_type, status, version DESC);

CREATE TABLE IF NOT EXISTS memory_review_log (
    review_id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('approve','reject','archive','supersede')),
    previous_status TEXT NOT NULL,
    new_status TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    reason TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memory_items(memory_id)
);

CREATE INDEX IF NOT EXISTS idx_memory_review_log_memory_time
ON memory_review_log(memory_id, reviewed_at DESC);
