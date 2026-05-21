# Phase 3: Observation To Human Review

Goal: move the SMR loop from `observation_only` toward auditable `pending_human_review` for a small number of high-quality candidates.

Implementation principles:

- Keep the existing SQLite, Markdown, registry, evidence graph, linter, and decision ledger architecture.
- Do not treat internal consensus proxy as official consensus.
- Do not allow stale news or filings to support strong conclusions.
- Do not let report text freely decide trade actions; structured promotion and candidate rules decide.

Tasks:

1. Local bootstrap script for an empty development runtime.
2. Source-level news ingestion, freshness, dedupe, and secondary evidence export.
3. Market/source/ticker-level filings ingestion, freshness, chunking, and primary evidence export.
4. Deterministic recommendation promotion rules for `observation_only -> candidate_shadow -> pending_human_review`.
5. Consensus proxy v2 fields and lint warn metadata for promotion blocking.
6. Recommendation candidate builder plus valuation and bear-case fields needed by promotion.
7. Unit tests and local smoke verification.
