# Phase 19 Non-core Gate Resolution Plan

**Goal:** explain why candidates remain conservative after core fundamentals blockers are cleared, and turn the remaining gates into ranked, actionable diagnostics.

**Baseline:** Phase 18 moved recovered financial statement fields into fundamentals snapshots and cleared core blockers for `00700.HK`, `300308.SZ`, and `688041.SH`.

## Scope

- Add a promotion block reason hierarchy.
- Diagnose filing freshness and evidence freshness.
- Add a Phase 19 evidence quality gate wrapper.
- Decompose bear case residual risk.
- Explain the `002230.SZ` thesis evidence gate.
- Validate recovered fundamentals promotion impact.
- Build a daily gate summary for `ai_core`.

## Non-Goals

- Do not loosen promotion rules.
- Do not create pending review items for unknown theses.
- Do not auto approve pending items.
- Do not create paper orders or paper positions.
- Do not remove or silently mitigate bear cases.
- Do not treat proxy EPS or internal proxy as official consensus.
- Do not expand `ai_core`.

## Architecture

Phase 19 is a read-mostly diagnostic layer. It reuses the latest Phase 14, Phase 18, Phase 6, fundamentals, evidence, and bear-case artifacts, then computes a single `primary_blocking_gate` plus secondary gates and next fixes.

The new hierarchy is intentionally separate from the promotion executor. It explains gate state without weakening existing thresholds or changing human-review behavior.

## New Artifacts

- `08_scripts/lib/smr_promotion_block_reason.py`
- `08_scripts/lib/smr_filing_freshness.py`
- `08_scripts/reporting/build_phase19_promotion_block_diagnostics.py`
- `08_scripts/reporting/build_phase19_filing_freshness_diagnostics.py`
- `08_scripts/reporting/build_phase19_evidence_quality_gate_summary.py`
- `08_scripts/reporting/build_phase19_bear_case_residual_risk.py`
- `08_scripts/reporting/build_phase19_thesis_evidence_gate.py`
- `08_scripts/verification/validate_phase19_recovered_fundamentals_promotion_impact.py`
- `08_scripts/reporting/build_phase19_daily_gate_summary.py`

## Gate Hierarchy

Supported gates:

- `DATA_FRESHNESS_GATE`
- `FILING_FRESHNESS_GATE`
- `EVIDENCE_QUALITY_GATE`
- `CORE_EVIDENCE_GATE`
- `NON_CORE_WARNING_GATE`
- `THESIS_CONFIDENCE_GATE`
- `VALUATION_GATE`
- `PROXY_SIGNAL_GATE`
- `BEAR_CASE_GATE`
- `PORTFOLIO_RISK_GATE`
- `REVIEW_STATE_GATE`
- `UNKNOWN_GATE`

Rules:

- A ticker with empty core blockers must not use `CORE_EVIDENCE_GATE` as primary.
- Unknown thesis stays blocked by `THESIS_CONFIDENCE_GATE`.
- Stale or missing filings block pending review.
- Critical or high unresolved bear cases block pending review.
- Medium partially mitigated bear cases can explain reduced-size pending only when existing gates allow it.
- Low or blocked evidence cannot support promotion.

## Validation

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/verification/validate_phase18_fundamentals_recovery_revalidation.py --tickers 00700.HK,300308.SZ,688041.SH --json
python 08_scripts/reporting/build_phase19_promotion_block_diagnostics.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase19_filing_freshness_diagnostics.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase19_evidence_quality_gate_summary.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase19_bear_case_residual_risk.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase19_thesis_evidence_gate.py --ticker 002230.SZ --json
python 08_scripts/verification/validate_phase19_recovered_fundamentals_promotion_impact.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase19_daily_gate_summary.py --watchlist ai_core --json
```
