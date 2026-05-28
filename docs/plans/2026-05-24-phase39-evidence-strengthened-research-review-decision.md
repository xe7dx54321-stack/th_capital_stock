# Phase 39 Evidence-Strengthened Research Review Decision Plan

> **For Codex:** Execute this plan task-by-task with verification checkpoints.

**Goal:** Use the five Phase 38 persisted `300308.SZ` evidence candidates to create an evidence-strengthened research packet and decide whether the ticker is a `research_review_candidate`, while keeping it out of investment pending.

**Architecture:** Phase 39 is a deterministic reporting and classification layer. It reuses Phase 38 evidence-chain refresh, post-persistence revalidation, and repair queue summaries. It adds contribution analysis and research-review classification, but it does not fetch sources, write investment decisions, or change promotion rules.

## Scope

- Main ticker: `300308.SZ`.
- Repair-only ticker: `300394.SZ`.
- Evidence source: Phase 38 persisted targeted candidates.
- New state: `research_review_candidate`, explicitly not `pending_human_review`.

## Guardrails

- No new watchlist or broad acquisition.
- No source fetching, raw cache writing, DB schema expansion, or generated HTML.
- Product mix is not confirmed ASP.
- Order visibility is not confirmed order.
- Shipment commentary is not a confirmed shipment number.
- Customer allocation proxy is not confirmed allocation.
- Internal proxy is not official consensus.
- `promotion_allowed=false`.
- `new_pending_created=0`.
- `paper_order_created=0`.
- No real trading path.

## Implementation Tasks

1. Add `smr_evidence_contribution_analyzer.py` to trace the five persisted Phase 38 evidence rows and explain what they support and do not support.
2. Add `build_phase39_300308_evidence_contribution.py` for JSON/Markdown contribution reports.
3. Add `build_phase39_300308_evidence_strengthened_packet.py` for before/after research packet refresh.
4. Add `smr_research_review_candidate.py` and `build_phase39_research_review_candidate_decision.py` for `research_review_candidate` classification.
5. Add `build_phase39_human_research_review_checklist.py` for human research questions and explicit non-goals.
6. Add `build_phase39_why_not_pending_reinforcement.py` to restate blockers after evidence strengthening.
7. Add `build_phase39_next_evidence_priority_update.py` to lower improved variables and keep missing sensitive variables high priority.
8. Add `build_phase39_300394_repair_status_summary.py` to keep `300394.SZ` in repair-only mode.
9. Add `build_phase39_review_decision_dashboard.py` to summarize both tickers.
10. Add Phase 39 tests for contribution boundaries, strengthened packet, review decision, checklist, why-not-pending, next evidence priority, repair status, and dashboard.

## Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase38_persistence_review_dashboard.py --json
python 08_scripts/reporting/build_phase39_300308_evidence_contribution.py --json
python 08_scripts/reporting/build_phase39_300308_evidence_strengthened_packet.py --json
python 08_scripts/reporting/build_phase39_research_review_candidate_decision.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase39_human_research_review_checklist.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase39_why_not_pending_reinforcement.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase39_next_evidence_priority_update.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase39_300394_repair_status_summary.py --json
python 08_scripts/reporting/build_phase39_review_decision_dashboard.py --json
```
