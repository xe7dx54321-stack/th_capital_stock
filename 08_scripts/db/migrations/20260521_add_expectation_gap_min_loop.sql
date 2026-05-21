-- Phase 2: recovery + expectation-gap minimum loop.

CREATE TABLE IF NOT EXISTS research_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id TEXT UNIQUE NOT NULL,
    report_id TEXT,
    recommendation_id TEXT,
    ticker TEXT,
    theme TEXT,
    claim_text TEXT NOT NULL,
    claim_type TEXT,
    importance TEXT NOT NULL,
    stance TEXT,
    confidence REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS evidence_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id TEXT UNIQUE NOT NULL,
    source_key TEXT,
    source_type TEXT,
    source_quality TEXT,
    source_status TEXT,
    published_at TEXT,
    ingested_at TEXT,
    text_excerpt TEXT,
    url_or_doc_id TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS claim_evidence_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    strength REAL,
    rationale TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(claim_id, evidence_id, relation_type)
);

CREATE TABLE IF NOT EXISTS consensus_revision_proxy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    market TEXT,
    period TEXT,
    metric TEXT,
    proxy_direction TEXT,
    proxy_magnitude REAL,
    confidence REAL,
    source_evidence_ids_json TEXT NOT NULL DEFAULT '[]',
    proxy_method TEXT,
    is_official_consensus INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS valuation_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    market TEXT,
    generated_at TEXT NOT NULL,
    valuation_available INTEGER NOT NULL DEFAULT 0,
    current_price REAL,
    market_cap REAL,
    pe_ttm REAL,
    ps_ttm REAL,
    pb REAL,
    historical_percentile REAL,
    peer_comparison_json TEXT NOT NULL DEFAULT '{}',
    valuation_status TEXT NOT NULL,
    missing_data_json TEXT NOT NULL DEFAULT '[]',
    allowed_usage TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);
