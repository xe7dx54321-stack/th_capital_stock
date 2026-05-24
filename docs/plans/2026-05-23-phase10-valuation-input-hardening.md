# Phase 10 Plan: Repair Resolution & Valuation Input Hardening

## Background

Phase 9 made the `09988.HK` blocker set explicit. The candidate remains below
`pending_human_review` because valuation inputs, data quality, and high bear
case response are not strong enough for promotion.

Phase 10 starts resolving the most actionable valuation blockers without
relaxing promotion rules.

## Goals

- Attempt real price and valuation freshness repair.
- Split price stale from valuation snapshot stale.
- Add a minimal auditable peer set for `09988.HK`.
- Add historical valuation percentile status with clear missing reasons.
- Allow internal proxy EPS as supporting evidence only.
- Improve bear case response summary and action effects.
- Add repair resolution checks that require validation before `resolved`.
- Revalidate `09988.HK` with before/after output.

## Non-goals

- No new complex agents.
- No real trade execution.
- No watchlist expansion.
- No promotion rule relaxation.
- No official consensus impersonation.
- No use of stale price for actionable valuation.
- No removal of high bear case just to create a pending item.

## Implementation

Phase 10 keeps valuation logic centralized in `smr_valuation.py`.

The valuation snapshot now records:

- `price_status` and `price_trade_date`.
- `peer_set_id`, `peer_set_status`, and peer availability.
- `historical_percentile_status` and metric-level missing reasons.
- `forward_eps.status`, with `internal_proxy` clearly marked.
- `inputs_used` metadata for auditability.

Repair execution remains conservative. `repair_valuation_snapshot.py --execute`
can refresh price data and recompute valuation, but repair queue tasks are not
marked `resolved` unless validation proves the original blocker disappeared.

## Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/reporting/build_phase8_blocker_triage.py --limit 10 --upsert-repair-queue
python 08_scripts/jobs/repair_valuation_snapshot.py --ticker 09988.HK --execute --json
python 08_scripts/jobs/run_phase10_repair_resolution.py --ticker 09988.HK --dry-run
python 08_scripts/verification/validate_phase10_repaired_candidate.py --ticker 09988.HK --days 365 --json
```

## Acceptance Criteria

- Compilation and unit tests pass.
- Phase 3 through Phase 8 validation scripts still run.
- `09988.HK` valuation repair outputs before/after.
- `PRICE_STALE` and `VALUATION_STALE` are separated.
- Peer set status, historical percentile status, and forward EPS status are
  visible.
- Proxy EPS is labelled `internal_proxy` and never official consensus.
- High bear case response remains promotion-blocking when unresolved.
- If `09988.HK` stays `candidate_shadow`, remaining blockers are more specific.

## Expected Post-phase Status

Phase 10 should move the project from broad blocker diagnosis to targeted
valuation input repair. Success does not require `09988.HK` to reach
`pending_human_review`; success means the remaining blockers are fewer, clearer,
and backed by auditable valuation inputs.
