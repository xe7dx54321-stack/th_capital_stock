# Phase 38 Targeted Evidence Candidate Review & Persistence Implementation Plan

> **For Codex:** Execute this plan task-by-task with verification checkpoints.

**Goal:** Turn Phase 37 dry-run evidence candidates for `300308.SZ` into reviewed, guarded, partially persisted research assets, while hardening the `300394.SZ` repair queue.

**Architecture:** Phase 38 is a thin orchestration layer over existing Phase 37 targeted acquisition and Phase 30 persistence guard. It does not add new connectors or broaden acquisition; it reviews the 15 existing candidates, persists a capped low-risk sample, refreshes evidence-chain/research-packet views, and writes only repair tasks for `300394.SZ`.

**Tech Stack:** Python CLI scripts, SQLite, existing SMR semantic evidence persistence, existing blocker repair queue, `unittest`.

---

## Scope

- Main ticker: `300308.SZ`.
- Repair ticker: `300394.SZ`.
- Candidate source: Phase 37 targeted dry-run candidate builder.
- Persistence route: Phase 30 semantic evidence candidate guard.
- Default persistence cap: 5 candidates.

## Guardrails

- No new watchlist.
- No new broad source fetching.
- No raw PDF, HTML, text cache, DB, log, or generated HTML committed.
- Product mix and margin commentary are not converted into confirmed ASP.
- Customer allocation proxy is never confirmed.
- Official consensus is not fabricated from internal proxy.
- `usable_for_promotion=false`.
- `new_pending_created=0`.
- `paper_order_created=0`.
- No real trading path.

## Implementation Tasks

### Task 1: Candidate Inventory

Create `08_scripts/lib/smr_targeted_candidate_inventory.py` and `08_scripts/reporting/build_phase38_300308_candidate_inventory.py`.

- Load Phase 37 dry-run candidates without writing DB state.
- Preserve `candidate_id`, `task_id`, `source_url`, `source_type`, `quoted_span`, usage, limitations, and warnings.
- Classify product mix separately from ASP when no explicit ASP/price language exists.

### Task 2: Candidate Quality Review

Create `08_scripts/lib/smr_targeted_candidate_quality_review.py` and `08_scripts/reporting/build_phase38_300308_candidate_quality_review.py`.

- Reuse Phase 30 quality scoring.
- Add sensitive-variable, duplicate, source, and quoted-span checks.
- Calibrate allowed usage after review.
- Keep customer allocation proxy out of default persistence.
- Strip full calibrated candidate payload from public JSON output.

### Task 3: Targeted Review Queue

Create `08_scripts/reporting/build_phase38_300308_targeted_review_queue.py`.

- Queue weak, sensitive, duplicate-risk, and ASP-without-explicit-price candidates.
- Generate dry-run commands only.
- Do not write queue state.

### Task 4: Guarded Persistence

Create `08_scripts/jobs/persist_phase38_300308_targeted_candidates.py`.

- Support `--dry-run` and `--execute`.
- Default cap is 5 candidates.
- Skip already persisted candidate IDs.
- Use Phase 30 guard before writing.
- Register snapshot only on execute.

### Task 5: Evidence Chain Refresh

Create `08_scripts/reporting/build_phase38_300308_evidence_chain_refresh.py`.

- Compare evidence-chain total before/after persisted Phase 38 candidates.
- Count new evidence by reviewed variable.
- Keep sensitive confirmed additions and promotion flags at zero.

### Task 6: Post-Persistence Revalidation

Create `08_scripts/verification/validate_phase38_300308_research_packet_post_persistence.py`.

- Report a conservative research quality delta.
- Keep quality at `medium_low` while supplier share, official consensus, and confirmed customer allocation remain missing.

### Task 7: Refreshed Packet

Create `08_scripts/reporting/build_phase38_300308_refreshed_packet_after_persistence.py`.

- Show before/after, new evidence count, variables improved, remaining missing variables, and why-not-pending.
- Do not output trade advice.

### Task 8: 300394 Repair Queue Hardening

Create `08_scripts/jobs/upsert_phase38_300394_repair_tasks.py` and `08_scripts/reporting/build_phase38_300394_repair_queue_summary.py`.

- Upsert five repair tasks for source inventory, text cache, semantic extraction, persistence guard, and generated state.
- Keep `research_deepening_allowed=false`.

### Task 9: Dashboard

Create `08_scripts/reporting/build_phase38_persistence_review_dashboard.py`.

- Summarize 300308 candidate handling, persistence count, review queue size, evidence after, research quality delta, and 300394 repair queue state.

### Task 10: Tests

Add Phase 38 unit tests for inventory, quality review, review queue, persistence, evidence-chain refresh, revalidation, refreshed packet, repair queue, and dashboard.

## Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase37_execution_dashboard.py --json
python 08_scripts/reporting/build_phase38_300308_candidate_inventory.py --json
python 08_scripts/reporting/build_phase38_300308_candidate_quality_review.py --json
python 08_scripts/reporting/build_phase38_300308_targeted_review_queue.py --json
python 08_scripts/jobs/persist_phase38_300308_targeted_candidates.py --dry-run --json
python 08_scripts/jobs/persist_phase38_300308_targeted_candidates.py --execute --limit 5 --json
python 08_scripts/reporting/build_phase38_300308_evidence_chain_refresh.py --json
python 08_scripts/verification/validate_phase38_300308_research_packet_post_persistence.py --json
python 08_scripts/reporting/build_phase38_300308_refreshed_packet_after_persistence.py --json
python 08_scripts/jobs/upsert_phase38_300394_repair_tasks.py --execute --json
python 08_scripts/reporting/build_phase38_300394_repair_queue_summary.py --json
python 08_scripts/reporting/build_phase38_persistence_review_dashboard.py --json
```
