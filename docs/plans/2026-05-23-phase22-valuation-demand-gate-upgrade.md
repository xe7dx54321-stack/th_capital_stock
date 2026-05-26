# Phase 22 Valuation Gate Upgrade + Confirmed Demand Evidence Escalation

## Goal

Phase 22 connects the Phase 21 direct-demand evidence layer to valuation gate
diagnostics while preserving the conservative promotion boundary:

- Upgrade valuation diagnostics into actionable blocker codes.
- Link demand evidence to revenue-growth assumptions.
- Escalate demand evidence into confirmed, tender/procurement, customer capex,
  management guidance, and industry-context buckets.
- Strengthen internal proxy source diagnostics.
- Revalidate promotion impact without automatically creating orders or pending
  review.

The phase does not add a full industry-chain agent, expand `ai_core`, loosen
promotion rules, treat indications as confirmed orders, or treat internal proxy
signals as official consensus.

## Baseline

Baseline commit:

```text
1981508dc551098bc080e33ca130f0b0750bdddc
phase21: expand demand evidence and proxy sources
```

Phase 21 status:

- Direct demand evidence is extracted and counted.
- `300308.SZ` and `688041.SH` have partially mitigated bear cases.
- `002230.SZ` remains weak on proxy evidence.
- Remaining gates are mainly `VALUATION_GATE`, `PROXY_SIGNAL_GATE`, and
  `BEAR_CASE_GATE`.
- No new pending review or real trading risk was introduced.

## Implementation

### Valuation Gate V2

New artifacts:

- `08_scripts/lib/smr_valuation_gate_v2.py`
- `08_scripts/reporting/build_phase22_valuation_gate_upgrade.py`

Behavior:

- Emits statuses from `blocked` to `promotion_supporting`.
- Splits valuation issues into codes such as `PRICE_STALE`,
  `PEER_COMPARISON_MISSING`, `HISTORICAL_VALUATION_WEAK`,
  `FORWARD_EPS_PROXY_ONLY`, `DEMAND_ASSUMPTION_UNSUPPORTED`, and
  `VALUATION_SUPPORTING_ONLY`.
- Keeps proxy EPS as internal/supporting only unless explicitly marked official
  consensus by upstream data.
- Allows `reduced_size_supporting` only as human-review support.

### Demand-to-Valuation Linkage

New artifacts:

- `08_scripts/lib/smr_demand_valuation_linkage.py`
- `08_scripts/reporting/build_phase22_demand_valuation_linkage.py`

Behavior:

- Maps direct demand evidence to revenue-growth and AI-demand assumptions.
- Allows signed contract, tender, and procurement evidence to provide strong
  support.
- Caps management commentary at medium support.
- Keeps rumor, missing evidence ids, and conflicting evidence from upgrading
  valuation assumptions.

### Confirmed Demand Evidence

New artifact:

- `08_scripts/reporting/build_phase22_confirmed_demand_evidence.py`

Behavior:

- Counts confirmed orders, tender/procurement evidence, framework agreements,
  customer capex, and management guidance.
- Explicitly explains why `confirmed_order_count=0`.
- Keeps customer capex as strong indication, not company-specific order.

### Proxy Strengthening V2

New artifact:

- `08_scripts/reporting/build_phase22_proxy_strengthening.py`

Behavior:

- Reuses Phase 21 demand-source expansion.
- Shows before/after proxy status and independent source count.
- Keeps all proxy output labelled as internal proxy only.
- Does not allow weak proxy to support pending review.

### Promotion Revalidation

New artifact:

- `08_scripts/verification/validate_phase22_valuation_demand_promotion_revalidation.py`

Behavior:

- Shows valuation, demand, proxy, and bear-case before/after status.
- Reports reduced-size pending eligibility when gates align.
- Does not automatically create `pending_human_review`.
- Keeps `paper_order_allowed=false`.

### Summary And Repair Queue

New artifacts:

- `08_scripts/reporting/build_phase22_valuation_demand_gate_summary.py`
- `08_scripts/jobs/upsert_phase22_valuation_demand_repair_tasks.py`

Behavior:

- Outputs JSON or Markdown summary.
- Lists remaining valuation blockers and next fixes.
- Converts confirmed-demand, valuation-support, forward-EPS, and proxy-source
  gaps into dry-run repair tasks.

## Expected Behavior

- Valuation gates can absorb demand evidence only as assumption support.
- Demand evidence does not replace valuation models.
- Indications do not become confirmed orders.
- Internal proxy and proxy EPS do not become official consensus.
- Context-only valuation, weak proxy, and high unresolved core bear case remain
  blockers.
- If pending review ever appears, it must be reduced-size, require human review,
  and disallow paper orders.

## Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase21_demand_proxy_gate_summary.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase22_valuation_gate_upgrade.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase22_demand_valuation_linkage.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase22_confirmed_demand_evidence.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase22_proxy_strengthening.py --watchlist ai_core --json
python 08_scripts/verification/validate_phase22_valuation_demand_promotion_revalidation.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase22_valuation_demand_gate_summary.py --watchlist ai_core --json
python 08_scripts/jobs/upsert_phase22_valuation_demand_repair_tasks.py --tickers 300308.SZ,688041.SH,002230.SZ --dry-run --json
```
