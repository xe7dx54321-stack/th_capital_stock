-- 按需采集内核：请求、执行、原始材料、标准化事实、候选证据和数据集状态。
-- last_checked_at 与 available_through 必须分开，避免把“刚轮询”误判为“数据已更新”。

CREATE TABLE IF NOT EXISTS acquisition_request (
    request_id TEXT PRIMARY KEY,
    workflow_run_id TEXT,
    entity_key TEXT NOT NULL,
    data_type TEXT NOT NULL,
    market TEXT NOT NULL,
    as_of TEXT,
    mode TEXT NOT NULL CHECK (mode IN ('cache_only', 'refresh_if_stale', 'force_refresh')),
    required_fields_json TEXT NOT NULL DEFAULT '[]',
    maximum_age_seconds INTEGER,
    minimum_authority TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    summary_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS acquisition_run (
    run_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES acquisition_request(request_id) ON DELETE CASCADE,
    provider_id TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    error_code TEXT,
    error_message TEXT,
    summary_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS source_document (
    document_id TEXT PRIMARY KEY,
    acquisition_request_id TEXT REFERENCES acquisition_request(request_id),
    source_id TEXT NOT NULL,
    entity_key TEXT NOT NULL,
    data_type TEXT NOT NULL,
    source_type TEXT NOT NULL,
    authority_tier TEXT NOT NULL,
    source_url TEXT,
    title TEXT NOT NULL,
    published_at TEXT,
    fetched_at TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    raw_text TEXT,
    raw_payload_json TEXT NOT NULL DEFAULT '{}',
    parser_version TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS normalized_fact (
    fact_id TEXT PRIMARY KEY,
    acquisition_request_id TEXT REFERENCES acquisition_request(request_id),
    entity_key TEXT NOT NULL,
    data_type TEXT NOT NULL,
    field_name TEXT NOT NULL,
    value_json TEXT NOT NULL,
    unit TEXT,
    period_start TEXT,
    period_end TEXT,
    as_of TEXT,
    source_document_id TEXT NOT NULL REFERENCES source_document(document_id),
    authority_tier TEXT NOT NULL,
    verification_status TEXT NOT NULL,
    confidence REAL NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_candidate (
    candidate_id TEXT PRIMARY KEY,
    acquisition_request_id TEXT REFERENCES acquisition_request(request_id),
    entity_key TEXT NOT NULL,
    data_type TEXT NOT NULL,
    claim_type TEXT NOT NULL,
    text TEXT NOT NULL,
    source_document_ids_json TEXT NOT NULL,
    authority_tier TEXT NOT NULL,
    occurred_at TEXT,
    usable_for_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dataset_state (
    entity_key TEXT NOT NULL,
    data_type TEXT NOT NULL,
    market TEXT NOT NULL,
    available_through TEXT,
    last_checked_at TEXT NOT NULL,
    last_successful_fetch_at TEXT,
    required_fields_present_json TEXT NOT NULL DEFAULT '[]',
    quality_status TEXT NOT NULL,
    is_complete INTEGER NOT NULL DEFAULT 0,
    source_ids_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (entity_key, data_type, market)
);

CREATE INDEX IF NOT EXISTS idx_acquisition_request_workflow ON acquisition_request(workflow_run_id, created_at);
CREATE INDEX IF NOT EXISTS idx_acquisition_run_request ON acquisition_run(request_id, started_at);
CREATE INDEX IF NOT EXISTS idx_source_document_entity ON source_document(entity_key, data_type, published_at);
CREATE INDEX IF NOT EXISTS idx_source_document_hash ON source_document(source_id, content_hash);
CREATE INDEX IF NOT EXISTS idx_normalized_fact_lookup ON normalized_fact(entity_key, data_type, field_name, as_of);
CREATE INDEX IF NOT EXISTS idx_evidence_candidate_entity ON evidence_candidate(entity_key, data_type, status);
