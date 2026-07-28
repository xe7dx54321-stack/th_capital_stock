CREATE TABLE IF NOT EXISTS research_graph_nodes (
    node_id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    entity_key TEXT,
    attributes_json TEXT NOT NULL DEFAULT '{}',
    valid_from TEXT,
    valid_until TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_research_graph_nodes_type_entity
ON research_graph_nodes(node_type, entity_key);

CREATE TABLE IF NOT EXISTS research_graph_edges (
    edge_id TEXT PRIMARY KEY,
    source_node_id TEXT NOT NULL,
    target_node_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    evidence_id TEXT,
    evidence_kind TEXT NOT NULL DEFAULT 'inference'
        CHECK (evidence_kind IN ('formal_fact','open_source','inference')),
    confidence REAL NOT NULL DEFAULT 0
        CHECK (confidence >= 0 AND confidence <= 1),
    valid_from TEXT,
    valid_until TEXT,
    attributes_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (source_node_id) REFERENCES research_graph_nodes(node_id),
    FOREIGN KEY (target_node_id) REFERENCES research_graph_nodes(node_id)
);

CREATE INDEX IF NOT EXISTS idx_research_graph_edges_source_relation
ON research_graph_edges(source_node_id, relation_type);

CREATE INDEX IF NOT EXISTS idx_research_graph_edges_target_relation
ON research_graph_edges(target_node_id, relation_type);

CREATE INDEX IF NOT EXISTS idx_research_graph_edges_evidence
ON research_graph_edges(evidence_id);
