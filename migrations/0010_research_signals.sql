CREATE TABLE IF NOT EXISTS research_signal_plans (
    plan_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    company_name TEXT,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active','completed','archived')),
    overall_confidence REAL NOT NULL DEFAULT 0
        CHECK (overall_confidence >= 0 AND overall_confidence <= 1),
    building_position_ready INTEGER NOT NULL DEFAULT 0
        CHECK (building_position_ready IN (0, 1)),
    source_run_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_research_signal_plans_ticker_status
ON research_signal_plans(ticker, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS research_signals (
    signal_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    current_state TEXT NOT NULL
        CHECK (current_state IN ('observing','first_confirm','double_confirm','invalidated')),
    importance REAL NOT NULL DEFAULT 0
        CHECK (importance >= 0 AND importance <= 1),
    monitor_frequency TEXT,
    threshold_json TEXT NOT NULL DEFAULT '{}',
    invalidation_json TEXT NOT NULL DEFAULT '{}',
    source_requirements_json TEXT NOT NULL DEFAULT '[]',
    last_evidence_id TEXT,
    last_observed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (plan_id, signal_id),
    FOREIGN KEY (plan_id) REFERENCES research_signal_plans(plan_id)
);

CREATE INDEX IF NOT EXISTS idx_research_signals_plan_state
ON research_signals(plan_id, current_state);

CREATE TABLE IF NOT EXISTS research_signal_observations (
    observation_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    signal_id TEXT NOT NULL,
    observed_state TEXT NOT NULL,
    evidence_id TEXT,
    evidence_source TEXT,
    observed_at TEXT NOT NULL,
    independent_from_previous INTEGER NOT NULL DEFAULT 0
        CHECK (independent_from_previous IN (0, 1)),
    note TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (plan_id, signal_id) REFERENCES research_signals(plan_id, signal_id)
);

CREATE INDEX IF NOT EXISTS idx_research_signal_observations_signal_time
ON research_signal_observations(plan_id, signal_id, observed_at DESC);
