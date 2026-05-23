# Phase 8 Plan: Repeated Blocker Triage + A/H Candidate Recovery

## Context

Phase 7 established continuous live reliability:

- `ai_core` can run 9 A/H/US tickers.
- Multi-ticker live validation can save run history and compare against the last run.
- A/H fundamentals extraction now records field-level values and missing reasons.
- Portfolio risk v1.5 can project exposure before candidate sizing.
- Promotion rules remain conservative.

The next bottleneck is not orchestration. The bottleneck is repeated blockers:
the same evidence, proxy, fundamentals, and risk gaps appear across live runs
without being converted into actionable repair tasks.

## Phase Goal

Phase 8 turns repeated blockers into a repair queue and starts A/H candidate
recovery, with `09988.HK` as the default target.

The goal is to answer:

- Which blockers keep recurring?
- Which tickers and markets do they affect?
- Which blockers are repairable first?
- What minimum fix path is required for an A/H candidate to move closer to
  `pending_human_review`?

## Non-goals

- Do not add Industry Chain Agent.
- Do not add Investment Committee Agent.
- Do not expand the watchlist beyond the current `ai_core` scope.
- Do not add real trade execution.
- Do not relax promotion rules.
- Do not treat internal proxy as official consensus.
- Do not allow low-quality evidence to support core claims.
- Do not silently ignore missing fundamentals.

## Design

### Stable Blocker Taxonomy

`smr_blocker_taxonomy.py` normalizes legacy promotion/debugger strings into
stable blocker codes:

- `FUNDAMENTALS_MISSING_FIELDS`
- `FILING_FRESHNESS_DEGRADED`
- `LIVE_NEWS_MISSING`
- `PROXY_WEAK`
- `PROXY_INVALID`
- `VALUATION_CONTEXT_ONLY`
- `VALUATION_NOT_PROMOTION_ELIGIBLE`
- `HIGH_BEAR_CASE`
- `DATA_QUALITY_RISK`
- `EVIDENCE_QUALITY_LOW`
- `PRIMARY_EVIDENCE_MISSING`
- `COUNTER_EVIDENCE_MISSING`
- `RISK_LIMIT_EXCEEDED`
- `THEME_EXPOSURE_LIMIT`
- `SECTOR_EXPOSURE_LIMIT`
- `MARKET_EXPOSURE_LIMIT`
- `LIQUIDITY_RISK`
- `UNKNOWN_BLOCKER`

The taxonomy also supplies type, severity, fixability, expected impact, and a
suggested fix.

### Repair Queue

`smr_blocker_repair_queue.py` creates `phase_blocker_repair_queue` and upserts
one active repair task per `watchlist_id + ticker + blocker_code`.

Repeated runs update source run IDs, affected fields, and metadata instead of
creating duplicate tasks.

### Phase 8 Triage Report

`build_phase8_blocker_triage.py` reads recent `phase_live_run_history`, finds
top repeated blockers, summarizes blockers per ticker, and optionally upserts
repair tasks.

### A/H Candidate Recovery

`validate_phase8_ah_candidate_recovery.py` defaults to `09988.HK`. It reruns the
single-ticker live pipeline, reads the latest fundamentals snapshot, emits
field-level extraction status, and converts blockers to repair tasks when
requested.

### A/H Fundamentals Hardening

The financial table extraction and filing chunk selector now include additional
HK/CN field synonyms and unit handling for simplified/traditional Chinese.
Sanity checks avoid treating percentages, growth rates, years, and notes as
monetary values.

### Portfolio Projection

`build_paper_portfolio_summary.py` now reports:

- Current exposure by theme, market, and sector.
- Pending approval scenario if all `pending_human_review` and
  `candidate_shadow` items are approved.
- Risk-adjusted scenario using portfolio-risk sizing.
- Exposure warnings and suggested downsize/delay actions.

## Acceptance Criteria

- Python compilation passes.
- Unit tests pass.
- Phase 3 controlled E2E remains green.
- Phase 4 NVDA live E2E remains green.
- Phase 5 paper portfolio smoke remains green or produces a clear skip reason.
- Phase 6 multi-ticker live validation runs with run history and comparison.
- Phase 7 run history summary can read recent runs.
- Phase 8 blocker triage outputs top repeated blockers.
- Repair queue creates at least 3 open repair tasks from recent runs.
- `09988.HK` recovery reports current status, promotion gap, field-level
  fundamentals extraction, structured blockers, and repair tasks.
- Paper portfolio summary outputs current, pending, and risk-adjusted exposure.
- Runbook remains normal multi-line Markdown.
- Promotion rules are not relaxed.
