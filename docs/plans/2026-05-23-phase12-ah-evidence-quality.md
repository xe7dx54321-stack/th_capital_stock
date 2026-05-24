# Phase 12 Plan: A/H Evidence Quality & Field Confidence Hardening

## Background

Phase 11 completed the peer and historical valuation layer for `09988.HK`.
The candidate still remained `candidate_shadow` because data quality and high
bear-case blockers were not clean enough for promotion.

Phase 12 hardens the A/H fundamentals field layer: source evidence linkage,
unit normalization, confidence scoring, derived fields, before/after reporting,
and bear-case response quality.

## Goals

- Reduce `DATA_QUALITY_RISK` for `09988.HK`.
- Reduce `MISSING_SOURCE_EVIDENCE_ID` and `AMBIGUOUS_UNIT`.
- Add field-level source linkage and confidence breakdowns.
- Normalize common A/H financial units without forcing ambiguous units.
- Ensure low-confidence or source-missing fields cannot become promotion
  evidence.
- Derive `gross_margin` and `free_cash_flow` only when inputs are usable and
  evidence-linked.
- Recalculate bear-case response with evidence-quality awareness.
- Revalidate `09988.HK` with before/after output.

## Non-goals

- No Industry Chain Agent.
- No Investment Committee Agent.
- No real trade execution.
- No watchlist expansion.
- No broad new data-source program.
- No promotion rule relaxation.
- No official consensus impersonation by proxy EPS.
- No low-quality evidence for core claims.
- No ambiguous unit forced into promotion evidence.
- No bear-case deletion to manufacture `pending_human_review`.

## Implementation

Phase 12 adds helper modules rather than rewriting the A/H table parser.

`smr_financial_units.py` normalizes common Chinese and English unit strings,
including RMB/HKD/USD million, thousand, ten-thousand, and hundred-million
scales. It blocks ambiguous units and prevents EPS, margin, and percentage
values from being treated as amount fields.

`smr_field_evidence_linkage.py` attaches field-level evidence only when a
direct or justified source mapping exists. Fields without evidence remain
context-only or blocked.

`smr_fundamentals_confidence.py` scores fields from mapping confidence, unit
confidence, source evidence, section type, period match, sanity checks, and
derived-input quality. The score maps to `promotion_evidence`,
`supporting_evidence`, `context_only`, or `blocked`.

`smr_derived_fundamentals.py` derives `gross_margin` and `free_cash_flow` with
input evidence IDs. Derived confidence is capped by the weakest input.

The Phase 12 report compares a pre-hardening fundamentals snapshot with a
fresh hardened snapshot. The validator then combines data quality, valuation,
bear-case response, candidate status, and repair queue resolution state.

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
python 08_scripts/verification/validate_phase12_evidence_quality_repaired_candidate.py --ticker 09988.HK --days 365 --json
```

## Acceptance Criteria

- Compilation and unit tests pass.
- Phase 3 through Phase 8 validation scripts still run.
- Phase 11 peer/historical validator still runs.
- `09988.HK` has at least five fundamentals fields with source evidence.
- `MISSING_SOURCE_EVIDENCE_ID` and `AMBIGUOUS_UNIT` are reduced in the
  before/after report.
- Confidence breakdowns are present for fundamentals fields.
- Low-confidence or source-missing fields cannot become promotion evidence.
- Derived fields include input evidence IDs when derivation succeeds.
- Bear-case response v3 includes evidence quality.
- `09988.HK` either remains `candidate_shadow` with more specific blockers or
  reaches `pending_human_review` only through unchanged gates.

## Expected Post-phase Status

Phase 12 should move the system from "peer and historical valuation inputs are
available" to "the A/H evidence and field-confidence layer can support higher
quality research judgments." Success does not require `09988.HK` to become
`pending_human_review`; success means the remaining blockers are more about
research judgment and unresolved bear-case risk than basic evidence plumbing.
