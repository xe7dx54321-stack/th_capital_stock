# Phase 20 Bear Case Evidence Mitigation + Valuation/Proxy Gate Strengthening

## Goal

Phase 20 addresses the higher-level gates surfaced by Phase 19 after core
fundamentals blockers were cleared:

- Bear Case Gate
- Valuation Gate
- Proxy Signal Gate
- Thesis Evidence Gate

The phase remains conservative. It does not loosen promotion rules, approve
reviews, create paper orders, or treat internal proxy data as official
consensus.

## Baseline

Baseline commit:

```text
72cb4f08818127226b87d52408b14e8c53ad7228
phase19: diagnose non-core gates and residual promotion blockers
```

Phase 19 status:

- `core_blocker_count=0`
- Filing freshness is fresh for `ai_core`.
- Evidence quality has no blocked evidence.
- Remaining primary gates are mainly `BEAR_CASE_GATE`, `VALUATION_GATE`,
  `REVIEW_STATE_GATE`, and `THESIS_CONFIDENCE_GATE`.
- `002230.SZ` has high metadata-simulated thesis confidence but insufficient
  claim/proxy/filing evidence for pending review.

## Implementation

### Bear Case Mitigation Evidence Mapper

New artifacts:

- `08_scripts/lib/smr_bear_case_mitigation.py`
- `08_scripts/reporting/build_phase20_bear_case_mitigation.py`

Behavior:

- Maps bear case categories to linked evidence.
- Allows financial statement evidence to mitigate revenue, margin, valuation,
  and data-quality risks.
- Does not allow financial statement evidence to directly mitigate order,
  demand, competitive, policy, supply-chain, or thesis-confidence risk.
- Keeps unresolved core bear cases blocking.
- Emits mitigation status, residual risk, evidence ids, missing evidence, and
  reduced-size eligibility diagnostics.

### Valuation Gate Strengthening

New artifacts:

- `08_scripts/lib/smr_valuation_gate.py`
- `08_scripts/reporting/build_phase20_valuation_gate_diagnostics.py`

Behavior:

- Splits valuation blockers into explicit codes such as `PRICE_STALE`,
  `PEER_COMPARISON_MISSING`, `HISTORICAL_VALUATION_MISSING`,
  `FORWARD_EPS_PROXY_ONLY`, and `VALUATION_CONFIDENCE_LOW`.
- Keeps proxy EPS labelled as internal proxy, never official consensus.
- Allows `supporting_evidence` to support reduced-size diagnostics only.
- Keeps `context_only`, `insufficient`, and `blocked` from supporting pending.

### Proxy Signal Gate Strengthening

New artifacts:

- `08_scripts/lib/smr_proxy_signal_gate.py`
- `08_scripts/reporting/build_phase20_proxy_signal_gate.py`

Behavior:

- Scores internal proxy signals by direction, recency, evidence quality,
  independent source count, thesis alignment, and conflict count.
- Requires at least two independent sources before a proxy signal can be
  `strong`.
- Labels every output as internal proxy only, not official sell-side consensus.
- Keeps weak, missing, invalid, and conflicted proxies out of promotion.

### 002230.SZ Evidence-backed Thesis Candidate

New artifact:

- `08_scripts/reporting/build_phase20_002230_thesis_evidence_pack.py`

Behavior:

- Separates metadata support from claim graph, proxy signal, and filing/news
  evidence.
- Can move `002230.SZ` from metadata-only to evidence-backed thesis candidate
  when non-metadata evidence exists.
- Keeps `allow_pending=false` when dominant proxy signal or direct thesis
  evidence is insufficient.

### Promotion Revalidation

New artifact:

- `08_scripts/verification/validate_phase20_promotion_revalidation.py`

Behavior:

- Shows before/after status for bear case, valuation, proxy, and thesis
  evidence gates.
- Counts gate improvements.
- Does not create pending review unless all existing gates truly pass.
- Keeps `paper_order_allowed=false`.

### Research Gate Summary

New artifact:

- `08_scripts/reporting/build_phase20_research_gate_summary.py`

Behavior:

- Summarizes Phase 20 gate improvements.
- Shows current main gate by ticker.
- Provides JSON and Markdown output.

## Validation

Run:

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase19_daily_gate_summary.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase20_bear_case_mitigation.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase20_valuation_gate_diagnostics.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase20_proxy_signal_gate.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase20_002230_thesis_evidence_pack.py --json
python 08_scripts/verification/validate_phase20_promotion_revalidation.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase20_research_gate_summary.py --watchlist ai_core --json
```

## Safety Constraints

- No promotion rule relaxation.
- No real trading.
- No automatic human-review approval.
- No paper order or paper position generation.
- No high unresolved core bear case can become pending.
- No weak proxy can support pending.
- No valuation `context_only` result can support pending.
