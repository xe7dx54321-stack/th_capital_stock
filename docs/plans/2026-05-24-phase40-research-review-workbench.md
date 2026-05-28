# Phase 40 Research Review Workbench Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect the Phase 39 `300308.SZ` `research_review_candidate` decision to a research-only workbench queue with guarded actions, audit logging, specific evidence requests, dashboarding, and post-action validation.

**Architecture:** Phase 40 adds a deterministic SQLite-backed research-review layer. Phase 39 remains the evidence and decision source of truth; Phase 40 stores only lifecycle status, audit records, and specific evidence requests, while reports assemble queue, packet, dashboard, and read-only HTML views.

**Tech Stack:** Python, SQLite, existing SMR reporting/job/verification scripts, `unittest`.

---

## Scope

- Main ticker: `300308.SZ`.
- Repair-only ticker: `300394.SZ`.
- New research-only state: lifecycle, queue, actions, audit, specific evidence request.
- Optional static HTML is generated only under ignored paths such as `09_runbooks/generated/`.

## Guardrails

- `research_review_candidate` is not `pending_human_review`.
- `in_research_review` and reviewed states are not approvals.
- `mark_reviewed` does not approve investment pending.
- `request_deeper_research` does not create pending or paper orders.
- `request_specific_evidence` creates a request task only; it does not fetch or write evidence.
- Supplier share, customer allocation, official consensus, ASP, orders, and shipments are not confirmed by Phase 40 actions.
- `pending_created=0`.
- `paper_order_created=0`.
- `promotion_allowed=false`.
- No broker adapter or real trading path is added.
- Raw/cache/DB/log/generated HTML artifacts are not committed.

## Implementation Tasks

1. Add `smr_research_review_lifecycle.py` for lifecycle statuses, transition validation, and lifecycle persistence.
2. Add `smr_research_review_queue.py` to queue `300308.SZ` and keep `300394.SZ` repair-only.
3. Add `build_phase40_research_review_queue.py` for JSON/Markdown queue output.
4. Add `build_phase40_research_review_workbench_packet.py` to combine Phase 39 strengthened packet, checklist, why-not-pending, and next evidence priorities.
5. Add `smr_research_review_actions.py` and `apply_phase40_research_review_action.py` for guarded dry-run/execute actions.
6. Add `smr_research_review_audit.py` and `build_phase40_research_review_audit_report.py` for append-only action audit.
7. Add `smr_specific_evidence_request.py` and `build_phase40_specific_evidence_requests.py` for specific evidence request generation.
8. Add `build_phase40_research_review_dashboard.py` to summarize queue, lifecycle, repair, and safety state.
9. Add `validate_phase40_research_review_post_action.py` to assert action safety after execute.
10. Add `build_phase40_research_review_html.py` as a read-only static workbench page generator.
11. Add Phase 40 unit tests for lifecycle, queue, workbench packet, actions, audit, specific requests, dashboard, validation, and HTML.
12. Update `09_runbooks/smr-research-upgrade-progress.md`.

## Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase39_review_decision_dashboard.py --json
python 08_scripts/reporting/build_phase40_research_review_queue.py --json
python 08_scripts/reporting/build_phase40_research_review_workbench_packet.py --ticker 300308.SZ --json
python 08_scripts/jobs/apply_phase40_research_review_action.py --ticker 300308.SZ --action request_deeper_research --dry-run --json
python 08_scripts/jobs/apply_phase40_research_review_action.py --ticker 300308.SZ --action request_specific_evidence --evidence-type official_consensus --dry-run --json
python 08_scripts/jobs/apply_phase40_research_review_action.py --ticker 300308.SZ --action request_deeper_research --execute --json
python 08_scripts/reporting/build_phase40_research_review_audit_report.py --json
python 08_scripts/reporting/build_phase40_specific_evidence_requests.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase40_research_review_dashboard.py --json
python 08_scripts/verification/validate_phase40_research_review_post_action.py --json
python 08_scripts/reporting/build_phase40_research_review_html.py --output 09_runbooks/generated/phase40_research_review.html
```
