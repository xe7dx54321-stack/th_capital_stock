# Phase 36 Targeted Evidence Acquisition Plan v1

## Context

Phase 35 created single-stock research packets for `300394.SZ` and
`300308.SZ`. The packets made the current research state readable, but they did
not try to fetch missing evidence or push either ticker into pending review.

Phase 36 narrows the next step:

- `300308.SZ` receives the first targeted evidence acquisition plan because it
  already has partial semantic evidence coverage.
- `300394.SZ` receives evidence-chain-zero diagnostics and a repair plan because
  the current research packet has no usable evidence chain.

## Scope

Phase 36 adds a deterministic planning layer for:

- targeted evidence gap analysis
- evidence source route planning
- evidence acquisition task building
- `300308.SZ` focused evidence planning
- `300394.SZ` evidence-chain-zero diagnostics
- `300394.SZ` evidence repair planning
- acquisition readiness scoring
- evidence acquisition dashboarding

## Guardrails

Phase 36 is not an evidence execution, investment promotion, or trading phase.

Required invariants:

- No buy/sell/add/reduce recommendation.
- No target price.
- No return or position guidance.
- No new `pending_human_review`.
- No approved paper.
- No paper order or paper position.
- No source fetching by the acquisition task builders.
- No evidence candidate, lifecycle, or DB writes.
- Supplier share is not assumed to be publicly confirmable.
- Customer allocation is not assumed to be publicly confirmable.
- ASP is not fabricated from product-mix evidence.
- Internal proxy data is not treated as official consensus.
- `promotion_allowed=false`.
- `new_pending_created=0`.
- `paper_order_created=0`.
- No raw PDF, HTML, text cache, DB, log, or generated HTML artifacts are
  committed.

## Implementation

New library modules:

- `08_scripts/lib/smr_targeted_evidence_gap.py`
- `08_scripts/lib/smr_evidence_source_route_planner.py`
- `08_scripts/lib/smr_evidence_acquisition_task.py`
- `08_scripts/lib/smr_evidence_acquisition_readiness.py`
- `08_scripts/lib/smr_evidence_chain_diagnostics.py`

New reporting scripts:

- `08_scripts/reporting/build_phase36_targeted_evidence_gap.py`
- `08_scripts/reporting/build_phase36_evidence_source_routes.py`
- `08_scripts/reporting/build_phase36_evidence_acquisition_tasks.py`
- `08_scripts/reporting/build_phase36_300308_focused_evidence_plan.py`
- `08_scripts/reporting/build_phase36_300394_evidence_chain_diagnostics.py`
- `08_scripts/reporting/build_phase36_300394_evidence_repair_plan.py`
- `08_scripts/reporting/build_phase36_acquisition_readiness_score.py`
- `08_scripts/reporting/build_phase36_evidence_acquisition_dashboard.py`

New tests:

- `tests/test_phase36_targeted_evidence_gap.py`
- `tests/test_phase36_evidence_source_routes.py`
- `tests/test_phase36_evidence_acquisition_tasks.py`
- `tests/test_phase36_300308_focused_plan.py`
- `tests/test_phase36_300394_evidence_chain_diagnostics.py`
- `tests/test_phase36_300394_evidence_repair_plan.py`
- `tests/test_phase36_acquisition_readiness.py`
- `tests/test_phase36_dashboard.py`

## Expected Behavior

The `300308.SZ` gap analyzer should identify critical missing or insufficient
variables including supplier share, ASP proxy, customer allocation proxy,
official consensus, shipment, order visibility, and industry forecast.

The source route planner should explain realistic compliant routes without
pretending sensitive variables are confirmable from public sources.

The acquisition task builder should produce task IDs, route types, priorities,
query intents, expected outputs, allowed usage targets, limitations, and
`do_not_do` guardrails.

The readiness scorer should prioritize feasible, high-impact tasks such as ASP
evidence from company IR, while penalizing high-impact but low-availability
tasks such as supplier share and customer allocation.

The `300394.SZ` diagnostics should cover source inventory, real IR sources,
text cache, chunks, semantic extraction, semantic candidates, quality filters,
persistence, lifecycle state, variable pack readability, ticker mapping, and
local DB/state visibility.

The `300394.SZ` repair plan should remain planning-only and should not write
evidence or suggest direct execution.

## Validation

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase35_research_packet_dashboard.py --json
python 08_scripts/reporting/build_phase36_targeted_evidence_gap.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase36_evidence_source_routes.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase36_evidence_acquisition_tasks.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase36_300308_focused_evidence_plan.py --json
python 08_scripts/reporting/build_phase36_300394_evidence_chain_diagnostics.py --json
python 08_scripts/reporting/build_phase36_300394_evidence_repair_plan.py --json
python 08_scripts/reporting/build_phase36_acquisition_readiness_score.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase36_evidence_acquisition_dashboard.py --json
```
