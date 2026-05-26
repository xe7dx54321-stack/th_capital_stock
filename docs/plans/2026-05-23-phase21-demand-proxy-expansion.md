# Phase 21 Direct Demand Evidence + Independent Proxy Source Expansion

## Goal

Phase 21 turns the Phase 20 missing-evidence blockers into structured,
re-runnable evidence diagnostics:

- Direct demand / order / customer / capex evidence extraction.
- Independent proxy source expansion.
- Bear-case missing evidence to repair queue tasks.
- Demand evidence re-run through bear-case mitigation.
- Promotion revalidation and demand/proxy summary.

The phase remains conservative. It does not add a complex industry-chain agent,
expand `ai_core`, loosen promotion rules, auto-approve pending review, or create
real or paper trading actions.

## Baseline

Baseline commit:

```text
5d5b1a8fdd8bd127df9186a6959d1ae4812303f5
phase20: mitigate bear cases and strengthen valuation proxy gates
```

Phase 20 status:

- Bear case, valuation, proxy, and thesis evidence gates are explainable.
- `300308.SZ`, `688041.SH`, and `002230.SZ` still need stronger direct demand,
  order, customer, or independent source evidence.
- `002230.SZ` is an evidence-backed thesis candidate, but still lacks dominant
  proxy signal and independent source count.
- New pending review was not required or created.

## Implementation

### Direct Demand Evidence Schema

New artifact:

- `08_scripts/lib/smr_direct_demand_evidence.py`

Behavior:

- Classifies demand evidence into categories such as `customer_order`,
  `signed_contract`, `tender_award`, `downstream_capex`,
  `management_guidance`, `product_launch_demand`, and
  `rumor_or_unconfirmed`.
- Uses conservative strength levels from `confirmed_order` down to `blocked`.
- Requires `evidence_id` and `independent_source_key`.
- Keeps management commentary as supporting evidence only, not confirmed order.
- Blocks rumor or unconfirmed evidence.
- Stores only structured metadata and short excerpts, not raw files.

### Direct Demand Extractor

New artifacts:

- `08_scripts/jobs/build_direct_demand_evidence.py`
- `08_scripts/reporting/build_phase21_direct_demand_evidence_summary.py`

Behavior:

- Extracts demand evidence from existing `evidence_items` and
  `document_chunks`.
- Counts independent sources by source id, filing id, announcement id, news id,
  or source URL.
- Emits dominant direction, limitations, source quality, and usable gate flags.

### Proxy Source Expansion

New artifact:

- `08_scripts/reporting/build_phase21_proxy_source_expansion.py`

Behavior:

- Adds usable demand evidence to the internal proxy snapshot.
- Recomputes independent source count and proxy strength.
- Keeps every output labelled as internal proxy only, never official
  consensus.
- Prevents metadata from counting as an independent source.

### Repair Queue

New artifact:

- `08_scripts/jobs/upsert_bear_case_evidence_repair_tasks.py`

Behavior:

- Converts missing bear-case/proxy evidence into repair tasks.
- Supports dry-run and execute modes.
- Deduplicates by ticker, bear-case claim, and missing evidence.
- Stores gate metadata such as `BEAR_CASE_GATE` or `PROXY_SIGNAL_GATE`.

### Demand Evidence Bear-case Rerun

New artifact:

- `08_scripts/verification/validate_phase21_bear_case_demand_mitigation.py`

Behavior:

- Compares bear-case mitigation before and after direct demand evidence.
- Allows medium residual risk to support reduced-size diagnostics only.
- Keeps high unresolved core bear cases blocking.

### Promotion Revalidation

New artifact:

- `08_scripts/verification/validate_phase21_promotion_revalidation.py`

Behavior:

- Shows before/after gate impact across demand, proxy, bear-case, valuation,
  and promotion status.
- Does not create pending unless the full gate stack truly passes.
- Keeps `paper_order_allowed=false`.

### Demand / Proxy Summary

New artifact:

- `08_scripts/reporting/build_phase21_demand_proxy_gate_summary.py`

Behavior:

- Outputs JSON or Markdown.
- Shows direct demand evidence, proxy source count, bear-case status,
  promotion status, and next fix.
- Lists remaining missing evidence and suggested source classes.

## Expected Behavior

- `300308.SZ`, `688041.SH`, and `002230.SZ` can output direct demand evidence
  summaries.
- Demand evidence can improve proxy or bear-case diagnostics only when evidence
  ids and independent source keys exist.
- Weak product/news evidence does not become confirmed order.
- Internal proxy remains explicitly non-official.
- No weak proxy, high unresolved core bear case, or valuation context-only
  candidate can enter pending review.
- New pending review is not required; if it ever appears, it must be
  reduced-size, require human review, and disallow paper orders.

## Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase20_research_gate_summary.py --watchlist ai_core --json
python 08_scripts/jobs/build_direct_demand_evidence.py --tickers 300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase21_direct_demand_evidence_summary.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase21_proxy_source_expansion.py --tickers 300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/jobs/upsert_bear_case_evidence_repair_tasks.py --tickers 300308.SZ,688041.SH,002230.SZ --dry-run --json
python 08_scripts/verification/validate_phase21_bear_case_demand_mitigation.py --tickers 300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/verification/validate_phase21_promotion_revalidation.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase21_demand_proxy_gate_summary.py --watchlist ai_core --json
```
