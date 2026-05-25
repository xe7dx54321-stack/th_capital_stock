# Phase 14 Thesis-aware Gate Generalization Plan

## Goal

Phase 14 extends the Phase 13 thesis-aware evidence gate from the `09988.HK`
proof case to the `ai_core` multi-ticker workflow, while making reduced-size
pending fully auditable.

## Context

Phase 13 established that the same missing fields can have different severity:

- `valuation_rerating`: `capex` and `free_cash_flow` are optional warnings.
- `cash_flow_improvement`: `capex` and `free_cash_flow` are core blockers.

Phase 14 keeps that distinction and applies it across the daily live pipeline.
The work does not relax promotion rules and does not create paper orders.

## Architecture

Phase 14 adds a thin thesis-aware orchestration layer:

- `smr_thesis_inference.py` infers thesis type from structured context.
- `validate_phase14_thesis_aware_multi_ticker_live.py` reads `ai_core`,
  applies thesis inference and core/non-core classification, and writes an
  auditable snapshot.
- `smr_decision.py` normalizes review audit metadata for pending and
  reduced-size pending decisions.
- `build_paper_portfolio_summary.py` displays reduced-size pending only in
  projected exposure.
- `build_phase14_thesis_aware_daily_summary.py` turns the validation snapshot
  into JSON and Markdown daily review output.

## Thesis Inference Rules

The first inference layer is conservative:

- Valuation snapshot plus peer/historical support implies
  `valuation_rerating`.
- Cloud text, sector, or theme implies `cloud_growth`.
- Semiconductor compute, GPU, accelerator, or AI infrastructure themes imply
  `ai_infrastructure_demand`.
- Capex, FCF, operating cash flow, or cash-flow text implies
  `cash_flow_improvement`.
- Buyback or dividend text implies `shareholder_return`.
- Weak or ambiguous signals return `unknown`.

If confidence is below `0.5`, the candidate remains out of automatic pending
review and requires manual thesis review.

## Review Audit Rules

Every reduced-size pending item must expose:

- `primary_thesis_type`
- `thesis_inference_confidence`
- `promotion_mode`
- `position_policy`
- `core_blockers`
- `supporting_warnings`
- `optional_warnings`
- `data_quality_gate_status`
- `bear_case_status`
- `residual_risk_level`
- `requires_human_review=true`
- `auto_approval_allowed=false`
- `paper_order_allowed=false`

These fields are ledger metadata and review-detail fields, not approval
shortcuts.

## Portfolio Risk Visibility

Reduced-size pending is projected, not current exposure:

- Current exposure only counts open paper positions.
- Pending reduced-size candidates appear in
  `projected_exposure_if_reduced_size_approved`.
- Paper orders remain unavailable until a human reviewer approves the item.

## Repair Queue Rules

Optional warnings remain repairable:

- `optional_missing` is marked `non_blocking_warning=true`.
- `still_should_repair=true` remains in metadata.
- `core_missing` stays open and blocking for the relevant thesis.
- The same field can have different metadata under different theses.

## Validation

Required validation commands:

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase13_core_gate_repaired_candidate.py --ticker 09988.HK --days 365 --thesis valuation_rerating --json
python 08_scripts/verification/validate_phase13_core_gate_repaired_candidate.py --ticker 09988.HK --days 365 --thesis cash_flow_improvement --json
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase14_thesis_aware_daily_summary.py --watchlist ai_core --json
python 08_scripts/reporting/build_paper_portfolio_summary.py
```

## Acceptance Notes

Phase 14 succeeds when the system can explain, for every `ai_core` ticker,
what the current thesis is, what is core-blocking, what is non-core warning,
whether reduced-size pending is allowed, and where the audit trail lives.
