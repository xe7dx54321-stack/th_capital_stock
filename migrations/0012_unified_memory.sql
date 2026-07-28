ALTER TABLE memory_items ADD COLUMN tags_json TEXT;
ALTER TABLE memory_items ADD COLUMN project_id TEXT;
ALTER TABLE memory_items ADD COLUMN hit_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE memory_items ADD COLUMN last_hit_at TEXT;
ALTER TABLE memory_items ADD COLUMN session_id TEXT;
ALTER TABLE memory_items ADD COLUMN preference_source TEXT;
ALTER TABLE memory_items ADD COLUMN preference_explicit_ref TEXT;
ALTER TABLE memory_items ADD COLUMN conflict_flag INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_memory_items_entity
ON memory_items(entity_type, entity_id, memory_type);

CREATE INDEX IF NOT EXISTS idx_memory_items_status
ON memory_items(status);

CREATE INDEX IF NOT EXISTS idx_memory_items_session
ON memory_items(session_id);

CREATE TABLE IF NOT EXISTS memory_retrieval_log (
    retrieval_id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    retrieval_reason TEXT NOT NULL,
    retrieval_usage TEXT,
    retrieval_context_json TEXT,
    consumer TEXT,
    hit_count_snapshot INTEGER,
    FOREIGN KEY (memory_id) REFERENCES memory_items(memory_id)
);

CREATE INDEX IF NOT EXISTS idx_memory_retrieval_log_memory_time
ON memory_retrieval_log(memory_id, retrieved_at DESC);
