# Phase 13 Core vs Non-core Evidence Gate Plan

## Goal

Phase 13 makes promotion gates thesis-aware. The goal is not to relax
promotion rules, but to decide whether a remaining evidence gap is core to the
current thesis, supporting, optional, or unknown.

## Context

Phase 12 left `09988.HK` with a much stronger evidence base:

- Source evidence ids are linked for the tracked fundamentals fields.
- Unit ambiguity has been removed for the tracked fields.
- Fundamentals fields have confidence breakdowns.
- Peer and historical valuation inputs are available from Phase 11.
- Remaining field gaps are mainly `capex` and `free_cash_flow`.

The open question is whether `capex` and `free_cash_flow` are hard blockers for
the current thesis. They are optional for a valuation rerating thesis, but core
for a cash-flow improvement thesis.

## Architecture

Phase 13 adds three explicit gates:

- `smr_thesis_dependency.py` loads thesis requirements and classifies missing
  fields.
- `smr_data_quality_gate.py` turns data-quality root causes into core or
  non-core severity.
- `smr_bear_case_response.py` adds bear-case category, core-to-thesis, residual
  risk, and action effect.

Promotion and candidate building consume these gates only when they are
provided. Existing behavior remains the default for older flows.

## Thesis Dependency Rules

The first controlled config is:

- `valuation_rerating`: core fields include revenue, net income, equity, market
  cap, and price; capex and free cash flow are optional.
- `cash_flow_improvement`: operating cash flow, capex, and free cash flow are
  core.
- `cloud_growth`, `revenue_growth`, and `shareholder_return` are supported for
  first-pass inference and future extension.

Core always wins across multiple theses. If one thesis treats a field as
optional and another treats it as core, the field remains core.

## Promotion Calibration

The calibrated promotion rules are:

- Any `core_blocker` blocks `pending_human_review`.
- `unknown_warning` defaults to manual review rather than promotion.
- `supporting_warning` and `optional_warning` do not hard block, but lower
  confidence and remain visible.
- `degraded_core` or `blocked` data quality blocks promotion.
- `degraded_non_core` can allow reduced-size pending if valuation, proxy,
  bear-case, source evidence, and portfolio risk also pass.
- Partially mitigated bear cases can allow reduced-size pending only when no
  critical unresolved core risk remains.

## Reduced-size Pending Policy

Reduced-size pending is still human review, not approval:

- `promotion_status`: `pending_human_review`
- `promotion_mode`: `reduced_size_pending`
- `action`: `small_candidate`
- `position_policy`: `reduced_size`
- Size: `min(base_size * 0.5, max_reduced_size_pct)`
- Default cap: `1.0%`

This path still requires portfolio risk participation and cannot generate a
paper order directly.

## 09988.HK Expected Outcomes

For `valuation_rerating`:

- `capex` and `free_cash_flow` classify as optional warnings.
- Data quality becomes `degraded_non_core`.
- Bear-case response remains partially mitigated with medium residual risk.
- Reduced-size `pending_human_review` is allowed only if all other gates pass.

For `cash_flow_improvement`:

- `capex` and `free_cash_flow` classify as core blockers.
- Data quality becomes `degraded_core`.
- Candidate remains `candidate_shadow`.
- Repair queue remains open for those core missing fields.

## Verification

Run:

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase13_core_gate_repaired_candidate.py --ticker 09988.HK --days 365 --thesis valuation_rerating --json
python 08_scripts/verification/validate_phase13_core_gate_repaired_candidate.py --ticker 09988.HK --days 365 --thesis cash_flow_improvement --json
```

Acceptance requires the two thesis paths to disagree for the right reason:

- Valuation rerating: non-core warnings, possible reduced-size pending.
- Cash-flow improvement: core blockers, no pending review.
