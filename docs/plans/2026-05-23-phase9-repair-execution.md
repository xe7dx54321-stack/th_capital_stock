# Phase 9 Plan: Repair Execution & Candidate Recovery

## Background

Phase 8 turned repeated live blockers into a repair queue. The system can now
show that `09988.HK` is not blocked by a lack of all data; it is blocked by
specific remaining issues: stale valuation, data-quality risk, unresolved bear
case, and several missing A/H fundamentals fields.

## Goals

- Execute high-priority repair tasks instead of only summarizing them.
- Split umbrella valuation and data-quality blockers into repairable causes.
- Focus the first recovery pass on `09988.HK`.
- Rebuild valuation and fundamentals snapshots without fabricating missing
  inputs.
- Produce structured bear-case responses that keep unresolved risks blocking
  pending review.
- Return a before/after repaired-candidate validation payload.

## Non-goals

- Do not add Industry Chain Agent.
- Do not add Investment Committee Agent.
- Do not execute real trades.
- Do not expand the watchlist.
- Do not add large new data sources.
- Do not relax promotion rules.
- Do not treat internal proxy as official consensus.
- Do not bypass bear-case, evidence, or portfolio-risk gates.

## Tasks

1. Add valuation diagnostics and `repair_valuation_snapshot.py`.
2. Add data-quality diagnostics with field/evidence/source root causes.
3. Harden A/H fundamentals extraction for EPS, capex, free cash flow, and
   equity fields.
4. Add structured bear-case response and wire it into live validation.
5. Add `run_phase9_repair_queue.py` for dry-run and execute modes.
6. Add `validate_phase9_repaired_candidate.py` for `09988.HK` before/after.
7. Add tests and update the runbook.

## Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/reporting/build_phase8_blocker_triage.py --limit 10 --upsert-repair-queue
python 08_scripts/jobs/repair_valuation_snapshot.py --ticker 09988.HK --dry-run
python 08_scripts/reporting/build_phase9_data_quality_diagnostics.py --ticker 09988.HK --json
python 08_scripts/jobs/run_phase9_repair_queue.py --ticker 09988.HK --dry-run
python 08_scripts/verification/validate_phase9_repaired_candidate.py --ticker 09988.HK --days 365 --json
```

## Acceptance Criteria

- Python compilation passes.
- Unit tests pass.
- Phase 3 through Phase 8 validation scripts still run.
- Valuation repair reports specific sub-blockers such as `PRICE_STALE`,
  `FORWARD_EPS_MISSING`, `HISTORICAL_PERCENTILE_MISSING`, and
  `PEER_SET_MISSING`.
- Data quality diagnostics report field-level missing reasons and evidence
  issues with `evidence_id` where available.
- Bear-case response keeps unresolved high bear cases below pending review.
- Repair queue supports dry-run and execute without auto-resolving unresolved
  tasks.
- `09988.HK` repaired candidate validation reports before/after status,
  resolved blockers, remaining blockers, field repair status, and bear-case
  response.

## Expected Post-phase Status

Phase 9 should move the system from "repair queue exists" to "repair queue can
execute and produce finer, more actionable blockers." If `09988.HK` remains
`candidate_shadow`, the remaining blockers should be fewer and more precise
rather than broad umbrella warnings.
