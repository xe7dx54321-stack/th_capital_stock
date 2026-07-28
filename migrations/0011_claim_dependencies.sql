CREATE TABLE IF NOT EXISTS research_claim_versions (
    claim_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    entity_key TEXT NOT NULL,
    claim_type TEXT NOT NULL
        CHECK (claim_type IN ('fact','assumption','driver','model','output')),
    metric TEXT NOT NULL,
    value_json TEXT NOT NULL,
    unit TEXT,
    source TEXT,
    evidence_id TEXT,
    confidence REAL NOT NULL DEFAULT 0
        CHECK (confidence >= 0 AND confidence <= 1),
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active','disputed','superseded','invalidated')),
    source_run_id TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (claim_id, version)
);

CREATE INDEX IF NOT EXISTS idx_research_claim_versions_entity_metric
ON research_claim_versions(entity_key, metric, version DESC);

CREATE TABLE IF NOT EXISTS research_claim_dependencies (
    upstream_claim_id TEXT NOT NULL,
    downstream_claim_id TEXT NOT NULL,
    relation_type TEXT NOT NULL DEFAULT 'depends_on',
    created_at TEXT NOT NULL,
    PRIMARY KEY (upstream_claim_id, downstream_claim_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_research_claim_dependencies_downstream
ON research_claim_dependencies(downstream_claim_id);

CREATE TABLE IF NOT EXISTS research_claim_corrections (
    correction_id TEXT PRIMARY KEY,
    disputed_claim_id TEXT NOT NULL,
    user_reported_value_json TEXT,
    authoritative_value_json TEXT,
    authoritative_evidence_id TEXT,
    status TEXT NOT NULL
        CHECK (status IN ('pending','verified','conflicted','applied','rejected')),
    impact_json TEXT NOT NULL DEFAULT '{}',
    before_artifact_id TEXT,
    after_artifact_id TEXT,
    source_run_id TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_research_claim_corrections_claim_time
ON research_claim_corrections(disputed_claim_id, created_at DESC);
