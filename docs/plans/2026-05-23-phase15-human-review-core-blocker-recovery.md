# Phase 15 Human Review Workflow + Core Blocker Recovery

## Context

Phase 14 made thesis-aware promotion work across the `ai_core` watchlist. It
also allowed `09988.HK` to enter `pending_human_review` as a reduced-size
candidate under the `valuation_rerating` thesis. That item is intentionally
not approved automatically and cannot create a paper order before human
review.

Phase 15 turns that pending state into an auditable operating workflow.

## Goals

- Show review queue and review detail snapshots for pending recommendations.
- Add structured manual review actions.
- Record every review action in `human_review_actions` and decision ledger
  metadata.
- Keep paper order creation guarded behind `approved_paper`.
- Add a dry-run review-to-paper smoke validator for `09988.HK`.
- Produce recovery diagnostics for `00700.HK`, `300308.SZ`, and `688041.SH`.
- Explain why `002230.SZ` remains `unknown` thesis and suggest metadata
  patches without applying them automatically.
- Add a Phase 15 review operations summary.

## Non-goals

- No real trade execution.
- No automatic approval.
- No paper order from `pending_human_review`.
- No promotion rule relaxation.
- No hidden optional warnings.
- No proxy EPS impersonation as official consensus.

## Implementation

### Human Review Workflow

`08_scripts/lib/smr_human_review_workflow.py` provides shared helpers for
review queue items, review detail, recommendation id aliases, and dry-run or
execute handling of manual review actions.

The workflow supports:

- `approve_paper`
- `reject`
- `downgrade`
- `request_more_research`
- `reduce_position_size`
- `archive`

`approve_paper` is valid only from `pending_human_review`.
`reduce_position_size` cannot increase the current suggested position.

### Decision Ledger

`08_scripts/lib/smr_decision.py` now creates `human_review_actions` and records
review action metadata alongside the existing `recommendation_reviews` table.
Approved rows expose `paper_order_allowed=true`; pending rows keep it false.

### Paper Order Guard

`08_scripts/lib/smr_paper_portfolio.py` keeps the existing
`approved_recommendations` filter and adds a lower-level guard in
`create_order_for_approved_recommendation`. Even if a caller passes a pending
recommendation directly, order creation returns `blocked_not_approved`.

### Reporting And Validation

New scripts:

- `08_scripts/reporting/build_review_queue_snapshot.py`
- `08_scripts/jobs/apply_human_review_action.py`
- `08_scripts/verification/validate_phase15_review_to_paper_smoke.py`
- `08_scripts/verification/validate_phase15_core_blocker_recovery.py`
- `08_scripts/reporting/build_phase15_unknown_thesis_diagnostics.py`
- `08_scripts/reporting/build_phase15_review_ops_summary.py`

## Acceptance

- `09988.HK` reduced-size pending is visible in review queue.
- Dry-run approval writes no database changes.
- Execute approval writes human review action and decision ledger metadata.
- Paper order generation sees only `approved_paper`.
- Core blocker diagnostics show before/after field status.
- Unknown thesis diagnostics explain why pending is blocked.
- Phase 15 review ops summary lists review work, repair work, unknown thesis,
  and paper order guard status.
