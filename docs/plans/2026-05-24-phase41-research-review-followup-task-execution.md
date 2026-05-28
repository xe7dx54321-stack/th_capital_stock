# Phase 41 Research Review Follow-up Task Execution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert the Phase 40 `request_deeper_research` action for `300308.SZ` into concrete research-only follow-up evidence tasks for official consensus, supplier share, and confirmed customer allocation.

**Architecture:** Phase 41 is a task execution and route-planning layer. It reads Phase 40 lifecycle/audit state, writes specific evidence requests and follow-up audit records, and reports source availability and route boundaries without writing evidence or investment decisions.

**Tech Stack:** Python, SQLite, existing SMR reporting/job/verification modules, `unittest`.

---

## Scope

- Main ticker: `300308.SZ`.
- Repair-only ticker: `300394.SZ`, excluded from research follow-up tasks.
- Core gaps: `official_consensus`, `supplier_share`, `confirmed_customer_allocation`.
- Output is a research follow-up queue and source-route dashboard, not an investment memo.

## Guardrails

- Follow-up tasks are not investment approvals.
- Specific evidence requests are not evidence.
- Official consensus request is not confirmed official consensus.
- Internal proxy remains `supporting_context_only`.
- Supplier share remains scenario-only unless directly disclosed.
- Customer allocation proxy is not confirmed allocation.
- No pending review, approved paper, paper order, paper position, broker adapter, or real trade is created.
- No buy/sell/add/reduce recommendation, target price, or position guidance is generated.
- Raw/cache/DB/log/generated HTML artifacts are not committed.

## Implementation Tasks

1. Add `smr_research_followup_trigger.py` and a trigger summary report to detect Phase 40 follow-up states.
2. Extend `smr_specific_evidence_request.py` with availability, feasibility, allowed usage, and expected output metadata.
3. Add `execute_phase41_specific_evidence_requests.py` for dry-run and guarded execute of the three core evidence requests.
4. Add `smr_official_consensus_availability.py` and report output for authorized consensus source availability.
5. Add `smr_supplier_share_route.py` and report output for public availability caveats and scenario-only use.
6. Add `smr_customer_allocation_route.py` and report output for customer allocation proxy boundaries.
7. Add `smr_research_followup_queue.py` and queue report output.
8. Add `smr_research_followup_audit.py` and audit report output.
9. Add `validate_phase41_research_only_revalidation.py` to assert no confirmed sensitive variables, pending, orders, or promotion relaxation.
10. Add `build_phase41_followup_dashboard.py` and optional read-only static HTML.
11. Add Phase 41 unit tests and update the research upgrade runbook.

## Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase40_research_review_dashboard.py --json
python 08_scripts/reporting/build_phase41_followup_trigger_summary.py --json
python 08_scripts/jobs/execute_phase41_specific_evidence_requests.py --ticker 300308.SZ --dry-run --json
python 08_scripts/jobs/execute_phase41_specific_evidence_requests.py --ticker 300308.SZ --execute --json
python 08_scripts/reporting/build_phase41_official_consensus_availability.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase41_supplier_share_route.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase41_customer_allocation_route.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase41_research_followup_queue.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase41_followup_audit_report.py --json
python 08_scripts/verification/validate_phase41_research_only_revalidation.py --json
python 08_scripts/reporting/build_phase41_followup_dashboard.py --json
python 08_scripts/reporting/build_phase41_followup_html.py --output 09_runbooks/generated/phase41_followup.html
```
