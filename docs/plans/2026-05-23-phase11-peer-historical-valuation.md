# Phase 11 Plan: Peer Data & Historical Valuation Completion

## Background

Phase 10 fixed the stale price and stale valuation blockers for `09988.HK`.
The candidate still remained `candidate_shadow` because valuation inputs were
supporting-only and peer/historical references were incomplete.

Phase 11 completes the next valuation input layer: peer data, peer multiples,
historical valuation data, and field-level data-quality reduction for the A/H
candidate recovery path.

## Goals

- Complete `hk_internet_platforms` peer data for `09988.HK`.
- Raise peer availability from `0/2` toward at least `2/2`.
- Add peer-level and metric-level missing reasons.
- Build historical valuation data v1, prioritizing `ps_ttm` and `pb`.
- Add period-level historical fundamentals support for revenue and equity
  attempts.
- Reduce `09988.HK` valuation-related data-quality root causes.
- Recalculate valuation-related bear-case response from peer and historical
  valuation evidence.
- Revalidate `09988.HK` with before/after output.

## Non-goals

- No new complex agents.
- No real trade execution.
- No watchlist expansion.
- No broad new data-source program.
- No promotion rule relaxation.
- No proxy EPS impersonating official consensus.
- No strong relative valuation conclusion when peer data is partial.
- No historical high/low conclusion when percentile data is missing.
- No bear-case deletion to manufacture `pending_human_review`.

## Implementation

Phase 11 keeps valuation logic centralized in `smr_valuation.py`.

The peer builder refreshes lightweight peer inputs where available and then
reuses the valuation snapshot peer-set logic. A peer is counted only when it
has a price and at least one usable valuation multiple. Missing peer inputs are
kept at peer and metric level.

The historical valuation builder uses local factor history first and falls back
to auditable external valuation series where available. A historical metric is
usable only when it has enough samples; missing metrics remain visible but do
not block if another historical metric has become available.

The data-quality path records before/after root-cause deltas. `09988.HK`
company-level fields can use same-issuer BABA official fundamentals, while
per-share fields are intentionally not copied across listings.

The bear-case response update only partially mitigates valuation-related bear
case claims when peer or historical valuation evidence exists. It does not
remove high bear case risk or bypass promotion gates.

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
python 08_scripts/jobs/build_peer_valuation_data.py --ticker 09988.HK --json
python 08_scripts/jobs/build_historical_valuation_snapshot.py --ticker 09988.HK --json
python 08_scripts/verification/validate_phase11_peer_historical_repaired_candidate.py --ticker 09988.HK --days 365 --json
```

## Acceptance Criteria

- Compilation and unit tests pass.
- Phase 3 through Phase 8 validation scripts still run.
- `09988.HK` peer set resolves to `hk_internet_platforms`.
- Peer count improves from the Phase 10 baseline and reaches at least `2/2`
  when data is available.
- Peer missing reasons remain visible for unavailable peers or metrics.
- At least one historical valuation metric is available, preferably `ps_ttm`
  or `pb`.
- Data-quality diagnostics show before/after root-cause movement.
- Bear-case response can move from `unresolved` to `partially_mitigated` only
  when peer or historical valuation evidence exists.
- `09988.HK` either remains `candidate_shadow` with more specific blockers or
  reaches `pending_human_review` through normal gates only.

## Expected Post-phase Status

Phase 11 should move the system from "peer and historical valuation are
missing" to "peer and historical valuation are available or explainably
partial." Success does not require `09988.HK` to become
`pending_human_review`; success means the peer count, historical percentile,
data-quality deltas, and bear-case response are auditable and promotion rules
remain intact.
