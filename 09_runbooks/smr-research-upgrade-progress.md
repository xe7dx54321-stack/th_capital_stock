# SMR Research Upgrade Progress

- created_at: 2026-05-20 00:01:34
- owner: Codex / SMR engineering
- goal: Move the system from data collection and status display toward auditable live candidate generation and repeatable review.

## Principles

- Scripts handle deterministic work: fetch, clean, dedupe, slice, link, score, and persist evidence.
- High-intelligence agents handle research judgment: compare sources, identify gaps, write rebuttals, and explain thesis risk.
- Report-writing agents turn structured slices into a readable investment report.
- The front-end shows only the final conclusions, key actions, and clickable deep links.

## Stage Status

| Module | Goal | Status | Artifact | Validation | Notes |
|---|---|---:|---|---|---|
| Upgrade progress ledger | Keep the stage history readable and auditable | In progress | `09_runbooks/smr-research-upgrade-progress.md` | Update every phase with status and validation notes | Current file |
| Research synthesis skill | Encode shared reasoning patterns for gap analysis and thesis construction | Done | `09_runbooks/skills/smr-research-synthesis/` | `quick_validate.py` passes | Continue refining |
| Investment report writing skill | Produce stable deep-report structure | Done | `09_runbooks/skills/smr-investment-report-writing/` | `quick_validate.py` passes | Report spine in place |
| Hard evidence validation skill | Treat capex, orders, margins, competition, and other variables as audit targets | Done | `09_runbooks/skills/smr-hard-evidence-validation/` | `quick_validate.py` passes | Integrated into report prompt |
| Investment analyst agent | Research and judgment layer | Done | `12_smr_agents/profiles/hermes_investment_analyst.json` | Shadow run successful | Still enforce no source-free claims |
| Investment report writer | Assemble report from structured evidence | Done | `12_smr_agents/profiles/hermes_investment_report_writer.json` | Shadow run successful | Stable output and timeout handling |
| Evidence pack builder | Prepare reusable source packs | Done | `08_scripts/research/build_investment_evidence_pack.py` | Markdown/json pack generated | Handoff ready |
| Data freshness monitor | Unified daily_bar/news/filings/fundamentals freshness status | Done | `08_scripts/lib/smr_data_health.py` | Real DB output available | A/H/US data status tracked |
| Freshness gate | Block stale inputs before downstream work | Done | freshness gate helpers | Existing pipeline uses it | Keeps stale data out of live actions |
| Source registry enforcement | Filter disabled/planned sources out of evidence | Done | `08_scripts/lib/smr_source_registry.py` | Registry filters verified | Unknown sources remain explicit |
| Evidence checker | Gate core claims with evidence quality | Done | `08_scripts/lib/smr_research_quality.py` | Unit-tested | Deterministic, not generative |
| Report quality linter | Block stale or unsupported recommendations | Done | report metadata / lint snapshot | Unit-tested | Warns now carry promotion meaning |
| Recommendation state machine | Draft/candidate/pending/approved/rejected lifecycle | Done | `08_scripts/lib/smr_decision.py` | Unit-tested | Writes decision ledger |
| Human review service | Approve / reject / downgrade recommendation | Done | `recommendation_reviews` | Unit-tested | Front-end review flow ready |
| Decision ledger | Replayable recommendation lifecycle trail | Done | `decision_ledger` | Real DB entries present | Traceable recommendation history |
| Agent run audit trail | Capture every pipeline run and block reason | Done | `agent_runs` | Real DB entries present | Useful for postmortem |
| Daily system health report | Daily reliability summary | Done | `08_scripts/reporting/build_daily_system_health_report.py` | Validated on real data | Status reflects data health |

## Stage 5 Recap

Phase 5 completed a live candidate generation partial pass.

- Commit: `381ec98 phase5: enable live evidence promotion and paper portfolio smoke test`
- Stage: `Phase 5: Live candidate generation partial pass`
- NVDA live E2E: `partial_pass`
- NVDA status: `pending_human_review`
- NVDA action: `small_candidate`
- NVDA proxy quality: `strong`
- NVDA live news evidence: `4`
- NVDA live filing evidence: `4`
- NVDA fundamentals: `fresh`
- NVDA ledger written: `true`
- NVDA review queue visible: `true`
- Approval: `approve_paper` executed
- Paper order: `paper_order__phase4_live__NVDA` generated and executed
- Paper position: opened at `reference_price=219.51`

## Stage 6 Recap

Phase 6 expanded the live checkpoint into multi-ticker reliability with portfolio risk v1.

- Commit: `c0e8b1465881b9a6dbc505a39b1577a31f9d43b8`
- Stage: `Phase 6: Multi-ticker live reliability partial pass`
- Watchlist: `ai_core`
- Tickers: `NVDA`, `AVGO`, `MSFT`, `AMZN`, `09988.HK`, `00700.HK`, `300308.SZ`, `688041.SH`, `002230.SZ`
- Result: `pending_human_review=1`, `candidate_shadow=3`, `observation_only=5`
- Pending item: `NVDA`
- Portfolio risk v1 is now wired into candidate sizing.

## Stage 7 Goal

Phase 7 focuses on continuous live reliability and A/H data-quality hardening.

### Goals

1. Record every multi-ticker live run in a persistent run-history table.
2. Compare the current run against the previous run and explain improvements, regressions, and repeated blockers.
3. Extract A/H fundamentals at field level with explicit missing reasons.
4. Harden HK/CN filing table parsing so percentages, notes, and unit noise do not masquerade as values.
5. Add risk v1.5 with projected exposure and risk-adjusted sizing.
6. Keep the promotion rules unchanged.

### Acceptance Criteria

- `validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history` records a reusable run history.
- `build_phase7_live_run_history_summary.py` shows the recent runs and how they changed.
- At least 5 tickers have run-history rows.
- At least 2 A/H tickers have field-level fundamentals extraction or clear missing reasons.
- Paper portfolio summary shows current exposure, pending exposure, and exposure after risk-adjusted sizing.
- No rule relaxation is used to manufacture new `pending_human_review` items.

## Validation Log

| Time | Check | Result |
|---|---|---|
| 2026-05-20 00:01:34 | Initial progress table bootstrap | In progress |
| 2026-05-20 00:17:32 | `ready__300308.SZ__09988.HK` evidence pack | Pass |
| 2026-05-20 08:33:20 | `ready__300308.SZ__09988.HK` hard evidence task | Pass |
| 2026-05-20 21:51:14 | Variable digest layer | Pass |
| 2026-05-21 08:53:23 | Trusted research foundation database validation | Pass |
| 2026-05-22 00:00:00 | Phase 5 live candidate checkpoint | Pass |
| 2026-05-22 00:00:00 | Phase 6 multi-ticker live reliability checkpoint | Pass |
| 2026-05-23 00:00:00 | Phase 7 continuous reliability work started | In progress |
| 2026-05-23 18:02:50 | Phase 7 run history summary | Pass: 2 ai_core runs, 9 tickers per run, repeated blockers visible |
| 2026-05-23 18:02:50 | Phase 7 regression suite | Pass: 50 unit tests, 209 Python files compiled, Phase 3 E2E pass |

## Stage 8 Goal

Phase 8 focuses on repeated blocker triage and A/H candidate recovery.

Current Phase 7 state:

- Commit: `16a8904 phase7: add live run history and A/H fundamentals hardening`
- Stage: `Phase 7: Continuous live reliability partial pass`
- Watchlist: `ai_core`
- Result: `candidate_shadow=5`, `observation_only=4`, `pending_human_review=0`
- Promotion rules remain conservative.

### Goals

1. Read recent `phase_live_run_history` rows.
2. Normalize repeated blockers into stable blocker codes.
3. Rank blockers by frequency, affected tickers, severity, fixability, and expected impact.
4. Convert repeated blockers into `phase_blocker_repair_queue` tasks.
5. Run a focused `09988.HK` A/H candidate recovery validator.
6. Continue hardening HK/CN fundamentals field extraction.
7. Show current, pending, and risk-adjusted portfolio exposure.
8. Keep all promotion rules unchanged.

### Non-goals

- Do not add Industry Chain Agent.
- Do not add Investment Committee Agent.
- Do not execute real trades.
- Do not expand the watchlist beyond the current `ai_core` scope.
- Do not add large new data-source integrations.
- Do not manufacture new `pending_human_review` by lowering gates.
- Do not mark internal proxy as official consensus.
- Do not use low-quality evidence for core claims.
- Do not silently ignore missing fundamentals.

### New Artifacts

- `08_scripts/lib/smr_blocker_taxonomy.py`
- `08_scripts/lib/smr_blocker_repair_queue.py`
- `08_scripts/reporting/build_phase8_blocker_triage.py`
- `08_scripts/verification/validate_phase8_ah_candidate_recovery.py`
- `docs/plans/2026-05-23-phase8-repeated-blocker-triage.md`

### Acceptance Criteria

- `build_phase8_blocker_triage.py --limit 10 --upsert-repair-queue` outputs top repeated blockers.
- Repair queue creates at least 3 open tasks from recent live run history.
- `validate_phase8_ah_candidate_recovery.py --ticker 09988.HK --days 365 --upsert-repair-queue` reports field-level extraction and blockers.
- `09988.HK` either advances using live evidence or reports exact missing fields and repair tasks.
- HK/CN extraction handles revenue, gross profit, operating income, net income, EPS, OCF, capex, cash, debt, and equity with explicit missing reasons.
- Paper portfolio summary reports current exposure, pending approval scenario, and risk-adjusted scenario.
- Unit tests cover taxonomy, repair queue upsert, recovery payloads, HK synonym extraction, ambiguous percentage handling, and projected exposure.
- No promotion rule relaxation is used.

### Phase 8 Status

Status: `Phase 8: Repeated blocker triage and A/H recovery partial pass`

Completion commit:

- `phase8: add blocker triage and A/H candidate recovery`

### Phase 8 Validation Results

- Python compilation: `compiled 217 files`
- Unit tests: `59 tests OK`
- Phase 3 controlled E2E: `partial_pass`, controlled `NVDA` still reaches `pending_human_review`
- Phase 4 NVDA live E2E: command completed; current live result is `candidate_shadow` because live data quality, valuation, and bear-case blockers remain conservative
- Phase 5 paper portfolio smoke: `partial_pass`; latest smoke target is a controlled Phase 3 pending item and the script reports the incomplete approval/order/position trace clearly
- Phase 6 multi-ticker live: command completed with saved run history for 9 `ai_core` tickers
- Phase 7 run history summary: `run_count=4`
- Phase 8 blocker triage: top repeated blockers are `DATA_QUALITY_RISK`, `VALUATION_NOT_PROMOTION_ELIGIBLE`, and `HIGH_BEAR_CASE`
- Phase 8 repair queue: `repair_queue_open_count=48`
- Phase 8 `09988.HK` recovery: `candidate_shadow`, `proxy_quality=strong`, `fundamentals_status=fresh`, `valuation_usage=blocked_due_to_stale_price`
- `09988.HK` missing fields: `gross_profit`, `eps_basic`, `capex`, `free_cash_flow`, `shareholders_equity`
- `09988.HK` repair tasks created: `4`
- Paper portfolio summary: `current_exposure_total=1.5`, `pending_exposure_if_all_approved=11.0`, `exposure_after_risk_adjusted_sizing=12.5`, `open_position_count=1`
- Runbook line count: `189`
- Promotion rules: unchanged; no new `pending_human_review` was manufactured by lowering gates

### Phase 8 Current Interpretation

Phase 8 upgrades the project from passively recording repeated blockers to
turning them into a repair queue. The first A/H recovery target, `09988.HK`,
does not force promotion; it now reports field-level fundamentals gaps, stale
price valuation blockage, structured blockers, and repair tasks that can be
re-run after extraction fixes.

## Stage 9 Goal

Phase 9 focuses on repair execution and candidate recovery. It starts executing
the highest-priority Phase 8 repair tasks instead of adding more triage layers.

Current Phase 8 checkpoint:

- Commit: `437a48f57888b09644ad9b71ae7a84d696159d5c`
- Stage: `Phase 8: Repeated blocker triage and A/H recovery partial pass`
- Open repair tasks: `48`
- Top blockers: `DATA_QUALITY_RISK`, `VALUATION_NOT_PROMOTION_ELIGIBLE`, `HIGH_BEAR_CASE`
- Focus ticker: `09988.HK`
- Current `09988.HK` state: `candidate_shadow`, `proxy_quality=strong`, `fundamentals_status=fresh`

### Phase 9 Goals

1. Execute repair queue tasks in dry-run and execute modes.
2. Split valuation blockers into stale price, stale valuation, missing forward EPS, missing historical percentile, missing peer set, and low-confidence valuation.
3. Split data-quality risk into field, source, and evidence-level root causes.
4. Continue A/H fundamentals repair for `gross_profit`, `eps_basic`, `capex`, `free_cash_flow`, and `shareholders_equity`.
5. Add structured bear-case responses without bypassing risk gates.
6. Re-run `09988.HK` candidate validation with before/after blocker output.
7. Keep promotion rules unchanged.

### Phase 9 Non-goals

- Do not add Industry Chain Agent.
- Do not add Investment Committee Agent.
- Do not execute real trades.
- Do not expand the watchlist.
- Do not add large new data-source integrations.
- Do not lower promotion thresholds to manufacture pending review.
- Do not treat internal proxy as official consensus.
- Do not bypass bear-case, evidence, freshness, or portfolio-risk gates.

### Phase 9 New Artifacts

- `08_scripts/jobs/repair_valuation_snapshot.py`
- `08_scripts/reporting/build_phase9_data_quality_diagnostics.py`
- `08_scripts/lib/smr_bear_case_response.py`
- `08_scripts/jobs/run_phase9_repair_queue.py`
- `08_scripts/verification/validate_phase9_repaired_candidate.py`
- `docs/plans/2026-05-23-phase9-repair-execution.md`

### Phase 9 Acceptance Criteria

- `repair_valuation_snapshot.py --ticker 09988.HK --dry-run` outputs valuation diagnostics and specific sub-blockers.
- `build_phase9_data_quality_diagnostics.py --ticker 09988.HK --json` outputs root causes and field quality.
- `run_phase9_repair_queue.py --ticker 09988.HK --dry-run` shows planned repair actions without writing database changes.
- `validate_phase9_repaired_candidate.py --ticker 09988.HK --days 365 --json` outputs before/after candidate status.
- Unresolved high bear cases continue to block `pending_human_review`.
- No promotion rule relaxation is used.

### Phase 9 Validation Results

- Python compilation: `compiled 92 phase script files`
- Unit tests: `73 tests OK`
- Phase 3 controlled E2E: `partial_pass`; controlled `NVDA` still reaches `pending_human_review`
- Phase 4 NVDA live E2E: command completed with `NVDA.status=candidate_shadow`, `proxy_quality=strong`, `live_news_evidence=4`, `live_filing_evidence=4`, and conservative blockers for stale price, valuation, data quality, and high bear case
- Phase 5 paper portfolio smoke: `partial_pass`; current smoke target is a controlled pending item and the script reports missing approval/order/position trace stages clearly
- Phase 6 multi-ticker live: command completed for 9 `ai_core` tickers with `candidate_shadow=5`, `observation_only=4`, `pending_human_review=0`
- Phase 8 blocker triage: `run_count=6`; top blockers are `DATA_QUALITY_RISK`, `VALUATION_NOT_PROMOTION_ELIGIBLE`, and `HIGH_BEAR_CASE`
- Repair queue dry-run for `09988.HK`: `tasks_selected=3`, `tasks_executed=0`; planned actions are data-quality diagnostics, valuation repair, and fundamentals snapshot repair
- `09988.HK` valuation repair dry-run: `valuation_status=stale_price`, `allowed_usage=blocked_due_to_stale_price`, remaining sub-blockers are `PRICE_STALE`, `VALUATION_STALE`, `FORWARD_EPS_MISSING`, `HISTORICAL_PERCENTILE_MISSING`, and `PEER_SET_MISSING`
- `09988.HK` data quality diagnostics: `overall_data_quality_status=degraded`; root causes include `AMBIGUOUS_UNIT`, `FIELD_NOT_FOUND`, `FIELD_MAPPING_MISSING`, and `derived_field_missing_inputs`
- `09988.HK` bear-case response: `unresolved`, `action_effect=block_pending_review`
- `09988.HK` repaired candidate validation: `before_status=candidate_shadow`, `after_status=candidate_shadow`, `promotion_allowed=false`, `candidate_action=watch`, `decision_ledger_written=true`
- `09988.HK` fields still missing or unusable: `revenue` due to `ambiguous_unit`, `gross_profit`, `eps_basic`, `capex`, `free_cash_flow`, `shareholders_equity`, plus other lower-priority margin/return fields
- Promotion rules: unchanged; Phase 9 did not manufacture a new `pending_human_review`

### Phase 9 Current Interpretation

Phase 9 upgrades the project from "repair tasks exist" to "repair tasks can be
selected, diagnosed, and executed safely." The first A/H recovery target,
`09988.HK`, remains `candidate_shadow`, but the blockers are now more precise:
stale price and valuation, missing forward EPS, missing historical percentile,
missing peer set, unresolved high bear case, and field-level fundamentals
quality issues. A/H extraction was also hardened to reject paragraph numbers,
percent-change EPS noise, ambiguous currencies, and field values too far from
their field anchor.

## Stage 10 Goal

Phase 10 focuses on repair resolution and valuation input hardening. It starts
turning Phase 9's diagnostics into concrete valuation input repairs for
`09988.HK`.

Current Phase 9 checkpoint:

- Commit: `77e00791a3ca17cea7d913c304ea17a4a9f0d501`
- Stage: `Phase 9: Repair Execution & Candidate Recovery`
- `09988.HK`: `candidate_shadow`, `proxy_quality=strong`,
  `fundamentals_status=fresh`, `promotion_allowed=false`
- Main blockers: `PRICE_STALE`, `VALUATION_STALE`,
  `FORWARD_EPS_MISSING`, `HISTORICAL_PERCENTILE_MISSING`,
  `PEER_SET_MISSING`, `DATA_QUALITY_RISK`, and high bear case blockers

### Phase 10 Goals

1. Repair or refine `PRICE_STALE` and `VALUATION_STALE`.
2. Add a minimal auditable peer set for `09988.HK`.
3. Add historical valuation percentile status and missing reasons.
4. Support internal proxy EPS as labelled supporting evidence only.
5. Improve bear-case response summaries and action effects.
6. Require validation before repair queue tasks can be marked `resolved`.
7. Revalidate `09988.HK` with before/after output.

### Phase 10 Non-goals

- Do not add Industry Chain Agent.
- Do not add Investment Committee Agent.
- Do not execute real trades.
- Do not expand the watchlist.
- Do not add large new data sources.
- Do not relax promotion rules.
- Do not label internal proxy EPS as official consensus.
- Do not use stale price to support actionable valuation.
- Do not remove high bear case to manufacture pending review.

### Phase 10 New Artifacts

- `00_control/valuation_peer_sets.json`
- `08_scripts/jobs/run_phase10_repair_resolution.py`
- `08_scripts/verification/validate_phase10_repaired_candidate.py`
- `docs/plans/2026-05-23-phase10-valuation-input-hardening.md`

### Phase 10 Acceptance Criteria

- `repair_valuation_snapshot.py --ticker 09988.HK --execute --json` outputs
  before/after valuation repair.
- `09988.HK` valuation output includes `peer_set_status`,
  `historical_percentile_status`, and `forward_eps.status`.
- Proxy EPS is explicitly `internal_proxy` and never official consensus.
- Bear-case response includes status counts and action effect.
- Repair queue resolution marks `resolved` only after validation proves the
  original blocker disappeared.
- Promotion rules remain unchanged.

## Stage 11 Goal

Phase 11 focuses on peer data and historical valuation completion. Phase 10
fixed price and valuation freshness for `09988.HK`; Phase 11 makes the peer and
historical valuation inputs usable or explicitly explainable.

Current Phase 10 checkpoint:

- Commit: `a1acbf1569897f1f814b602b8f2276c075dab94c`
- Stage: `Phase 10: Repair Resolution & Valuation Input Hardening`
- `09988.HK`: `candidate_shadow`, `price_status=fresh`,
  `valuation_status=partial`, `allowed_usage=supporting_evidence`
- Peer set: `hk_internet_platforms`, previously configured but unavailable
- Historical valuation: previously `missing`
- Forward EPS: `internal_proxy`, supporting evidence only, not official
  consensus
- Main remaining blockers: `DATA_QUALITY_RISK`, peer/historical data gaps, and
  high bear case blockers

### Phase 11 Goals

1. Complete peer data for `hk_internet_platforms`.
2. Raise `09988.HK` peer availability from `0/2` toward at least `2/2`.
3. Add peer multiples and metric-level missing reasons.
4. Build historical valuation data v1, prioritizing `ps_ttm` or `pb`.
5. Add A/H historical fundamentals support for revenue and equity attempts.
6. Reduce `09988.HK` field-level data-quality root causes where possible.
7. Recalculate valuation-related bear-case response from live or stored
   valuation evidence.
8. Revalidate `09988.HK` without relaxing promotion rules.

### Phase 11 Non-goals

- Do not add Industry Chain Agent.
- Do not add Investment Committee Agent.
- Do not execute real trades.
- Do not expand the watchlist.
- Do not add large new data sources.
- Do not label proxy EPS as official consensus.
- Do not write strong cheap/expensive conclusions from partial peer data.
- Do not write historical high/low conclusions when percentile data is missing.
- Do not bypass portfolio risk, data quality, or high bear case gates.

### Phase 11 New Artifacts

- `08_scripts/jobs/build_peer_valuation_data.py`
- `08_scripts/jobs/build_historical_valuation_snapshot.py`
- `08_scripts/verification/validate_phase11_peer_historical_repaired_candidate.py`
- `docs/plans/2026-05-23-phase11-peer-historical-valuation.md`

### Phase 11 Checkpoint Results

- `09988.HK` peer set: `hk_internet_platforms`
- Peer count: `0/2` baseline to `4/2` after Phase 11 peer data completion
- Peer comparison: `supporting`
- Historical valuation: `available`
- Available historical metrics: `pb`, `pe_ttm`
- Historical fundamentals support: revenue is available from `factor_daily`;
  shareholders equity is attempted, with `book_value_per_share` present but
  shares outstanding still missing for period-level equity derivation
- Data-quality root causes reduced: `gross_profit`, `eps_basic`,
  `shareholders_equity`, and `gross_margin` moved from missing to extracted
  or confidence-review states
- Bear-case response: valuation rerating risk moves from `unresolved` to
  `partially_mitigated`, with action effect `reduce_position_size`
- Candidate status: still `candidate_shadow`
- Promotion rules: unchanged; no `pending_human_review` was manufactured

### Phase 11 Validation Commands

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

## Stage 12 Goal

Phase 12 focuses on A/H evidence quality and field confidence hardening. Phase
11 made `09988.HK` peer and historical valuation inputs available; Phase 12
raises the quality of the underlying fundamentals fields so valuation and bear
case responses are traceable and confidence-scored.

Current Phase 11 checkpoint:

- Commit: `332a32aa70f7e0c32eed60c4d92bc85bb54c4869`
- Stage: `Phase 11: Peer Data & Historical Valuation Completion`
- `09988.HK`: still `candidate_shadow`, `promotion_allowed=false`
- Peer set: `hk_internet_platforms`, `peer_count_available=4/2`
- Historical valuation: `available`, with `pb` and `pe_ttm`
- Bear-case response: `partially_mitigated`
- Main remaining blockers: `DATA_QUALITY_RISK`, `AMBIGUOUS_UNIT`,
  `MISSING_SOURCE_EVIDENCE_ID`, field confidence, and partially mitigated high
  bear case

### Phase 12 Goals

1. Link key A/H fundamentals fields to source evidence where justified.
2. Normalize A/H financial units with explicit confidence and blocked handling
   for ambiguous units.
3. Add field-level confidence breakdowns and allowed usage.
4. Ensure derived fields inherit input evidence and never outrank their inputs.
5. Add Phase 12 data-quality before/after reporting.
6. Recalculate bear-case response with evidence-quality awareness.
7. Revalidate `09988.HK` without relaxing promotion rules.

### Phase 12 Non-goals

- Do not add new complex agents.
- Do not execute real trades.
- Do not expand the watchlist.
- Do not add a broad new data-source program.
- Do not label proxy EPS as official consensus.
- Do not allow fields without `source_evidence_id` to support promotion.
- Do not force ambiguous units into valuation or core bear-case responses.
- Do not delete high bear case claims to manufacture `pending_human_review`.

### Phase 12 New Artifacts

- `08_scripts/lib/smr_financial_units.py`
- `08_scripts/lib/smr_field_evidence_linkage.py`
- `08_scripts/lib/smr_fundamentals_confidence.py`
- `08_scripts/lib/smr_derived_fundamentals.py`
- `08_scripts/reporting/build_phase12_data_quality_before_after.py`
- `08_scripts/verification/validate_phase12_evidence_quality_repaired_candidate.py`
- `docs/plans/2026-05-23-phase12-ah-evidence-quality.md`

### Phase 12 Checkpoint Results

- `09988.HK` fields with source evidence: at least 15 after hardening.
- `MISSING_SOURCE_EVIDENCE_ID`: reduced from field-level root causes to zero
  in the Phase 12 before/after report.
- `AMBIGUOUS_UNIT`: reduced from field-level root causes to zero in the Phase
  12 before/after report.
- Field confidence now includes breakdowns for mapping, unit, source evidence,
  section type, period match, and sanity checks.
- `gross_margin` is derived from hardened `gross_profit` and `revenue` inputs
  with inherited evidence.
- `free_cash_flow` remains blocked because `capex` is still missing; the
  missing input is explicit.
- Bear-case response remains `partially_mitigated`; valuation/data-quality
  evidence improves, but high bear case still prevents pending review.
- Candidate status remains `candidate_shadow`.
- Promotion rules remain unchanged; no `pending_human_review` was manufactured.

### Phase 12 Validation Commands

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

## Stage 13 Goal

Phase 13 adds a thesis-aware core vs non-core evidence gate. Phase 12 fixed
field traceability, unit ambiguity, and confidence scoring; Phase 13 decides
whether a remaining field gap is actually core to the current investment
thesis.

Current Phase 12 checkpoint:

- Commit: `15f8d34d2e3932c452463b9767010e35b498cfd4`
- Stage: `Phase 12: A/H Evidence Quality & Field Confidence Hardening`
- Source evidence id gaps: reduced to zero for the tracked Phase 12 fields
- Ambiguous unit root causes: reduced to zero
- Remaining blockers: `DATA_QUALITY_RISK`, `FIELD_NOT_FOUND`, and
  `HIGH_BEAR_CASE_PARTIALLY_MITIGATED`
- Remaining missing fields for `09988.HK`: `capex` and `free_cash_flow`
- Candidate status: still `candidate_shadow`, with promotion rules unchanged

### Phase 13 Goals

1. Add a thesis dependency map for required, supporting, and optional fields.
2. Classify missing fields as `core_blocker`, `supporting_warning`,
   `optional_warning`, or `unknown_warning`.
3. Recalibrate `DATA_QUALITY_RISK` into core and non-core severities.
4. Add bear-case severity metadata: category, core-to-thesis flag, residual
   risk level, and action effect.
5. Add a strict reduced-size pending policy for cases with no core blocker.
6. Revalidate `09988.HK` under both `valuation_rerating` and
   `cash_flow_improvement` theses.
7. Keep optional missing fields in warnings and repair queue metadata rather
   than treating them as resolved.

### Phase 13 Non-goals

- Do not loosen promotion rules globally.
- Do not ignore optional missing fields.
- Do not downgrade core missing fields to warnings.
- Do not delete or weaken high bear cases.
- Do not treat internal proxy EPS as official consensus.
- Do not bypass portfolio risk or human review.

### Phase 13 New Artifacts

- `00_control/thesis_evidence_requirements.json`
- `08_scripts/lib/smr_thesis_dependency.py`
- `08_scripts/lib/smr_data_quality_gate.py`
- `08_scripts/verification/validate_phase13_core_gate_repaired_candidate.py`
- `docs/plans/2026-05-23-phase13-core-vs-noncore-gate.md`

### Phase 13 Expected 09988.HK Behavior

- Under `valuation_rerating`, `capex` and `free_cash_flow` are
  `optional_warning`; they do not block reduced-size human review, but remain
  visible in warnings and repair queue metadata.
- Under `cash_flow_improvement`, `capex` and `free_cash_flow` are
  `core_blocker`; they continue to block `pending_human_review`.
- `DATA_QUALITY_RISK` can become `degraded_non_core` only when remaining
  issues are not thesis-core.
- Partially mitigated bear cases can reduce position size, but unresolved core
  risks still block pending review.

### Phase 13 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/reporting/build_phase8_blocker_triage.py --limit 10 --upsert-repair-queue
python 08_scripts/verification/validate_phase11_peer_historical_repaired_candidate.py --ticker 09988.HK --days 365 --json
python 08_scripts/verification/validate_phase12_evidence_quality_repaired_candidate.py --ticker 09988.HK --days 365 --json
python 08_scripts/verification/validate_phase13_core_gate_repaired_candidate.py --ticker 09988.HK --days 365 --thesis valuation_rerating --json
python 08_scripts/verification/validate_phase13_core_gate_repaired_candidate.py --ticker 09988.HK --days 365 --thesis cash_flow_improvement --json
```

## Stage 14 Goal

Phase 14 generalizes the thesis-aware gate from the single `09988.HK`
Phase 13 proof to the `ai_core` multi-ticker workflow. The goal is not to
create more pending recommendations, but to make each ticker explain its
primary thesis, core blockers, non-core warnings, and reduced-size review
audit trail.

Current Phase 13 checkpoint:

- Commit: `6ed2452f4e74638a0742d091b497ae045ec77ad0`
- Stage: `Phase 13: Thesis-aware promotion gate completed`
- `09988.HK` under `valuation_rerating`: reduced-size
  `pending_human_review`
- `09988.HK` under `cash_flow_improvement`: still `candidate_shadow`
- `capex` and `free_cash_flow`: optional warnings for valuation rerating,
  core blockers for cash-flow improvement
- Reduced-size pending remains human review only; no auto approval and no
  paper order

### Phase 14 Goals

1. Add conservative thesis inference from claims, candidate context, proxy,
   valuation, bear case, market signal, and watchlist metadata.
2. Add an independent Phase 14 multi-ticker validator for `ai_core`.
3. Keep the original Phase 6 live validator behavior unchanged by default.
4. Add review and decision-ledger audit fields for reduced-size pending.
5. Show reduced-size pending in paper portfolio projected exposure only, not
   current exposure.
6. Add a Phase 14 daily summary with thesis, core blockers, non-core warnings,
   unknown thesis, and next action.
7. Keep optional missing fields in the repair queue as non-blocking warnings,
   not resolved tasks.

### Phase 14 Non-goals

- Do not expand the `ai_core` watchlist.
- Do not add new complex agents.
- Do not loosen promotion rules.
- Do not delete bear cases.
- Do not treat proxy EPS as official consensus.
- Do not auto approve reduced-size pending.
- Do not create paper orders before human approval.
- Do not hide optional warnings.

### Phase 14 New Artifacts

- `08_scripts/lib/smr_thesis_inference.py`
- `08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py`
- `08_scripts/reporting/build_phase14_thesis_aware_daily_summary.py`
- `docs/plans/2026-05-23-phase14-thesis-aware-generalization.md`

### Phase 14 Expected Behavior

- Every `ai_core` ticker gets a `primary_thesis_type` or `unknown`.
- `unknown` thesis cannot create `pending_human_review`.
- `core_blockers` continue to block pending review.
- `optional_warnings` and `supporting_warnings` remain visible in ledger,
  daily summary, and repair queue metadata.
- `09988.HK` can remain reduced-size pending under inferred
  `valuation_rerating` only if the strict Phase 13 gates still pass.
- Reduced-size pending shows `requires_human_review=true`,
  `auto_approval_allowed=false`, and `paper_order_allowed=false`.

### Phase 14 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase13_core_gate_repaired_candidate.py --ticker 09988.HK --days 365 --thesis valuation_rerating --json
python 08_scripts/verification/validate_phase13_core_gate_repaired_candidate.py --ticker 09988.HK --days 365 --thesis cash_flow_improvement --json
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase14_thesis_aware_daily_summary.py --watchlist ai_core --json
python 08_scripts/reporting/build_paper_portfolio_summary.py
```

## Stage 15 Goal

Phase 15 hardens the human review workflow that follows Phase 14 reduced-size
pending recommendations. The focus is operational safety: a reviewer can see
why an item is pending, choose a structured action, and only an explicit
`approve_paper` transition can later create a paper portfolio order.

Current Phase 14 checkpoint:

- Commit: `d2670cc37a9d2d7bb7f4f814243eb2e97068f4e0`
- Stage: `Phase 14: Thesis-aware Gate Generalization + Review Workflow Hardening`
- `09988.HK` under inferred `valuation_rerating`: reduced-size
  `pending_human_review`
- `09988.HK` has `requires_human_review=true`,
  `auto_approval_allowed=false`, and `paper_order_allowed=false` before
  approval
- Core blocker tickers remain `00700.HK`, `300308.SZ`, and `688041.SH`
- `002230.SZ` remains `unknown` thesis and cannot enter pending review

### Phase 15 Goals

1. Add review queue and review detail snapshots with thesis, field warnings,
   bear-case residual risk, portfolio impact, and hard audit flags.
2. Add structured manual review actions: `approve_paper`, `reject`,
   `downgrade`, `request_more_research`, `reduce_position_size`, and
   `archive`.
3. Write every review action to both `human_review_actions` and the decision
   ledger.
4. Enforce that only `pending_human_review` can become `approved_paper`.
5. Enforce that only `approved_paper` can create paper orders.
6. Add a dry-run review-to-paper smoke validator for `09988.HK`.
7. Add recovery diagnostics for `00700.HK`, `300308.SZ`, and `688041.SH`
   core blockers.
8. Add unknown-thesis diagnostics for `002230.SZ`.
9. Add a daily review operations summary for review and repair work.

### Phase 15 Non-goals

- Do not perform real trading.
- Do not auto approve reduced-size pending.
- Do not create paper orders from `pending_human_review`.
- Do not let `candidate_shadow`, `observation_only`, `rejected`,
  `needs_more_research`, or `archived` create paper orders.
- Do not hide optional warnings.
- Do not loosen promotion rules.
- Do not treat proxy EPS as official consensus.

### Phase 15 New Artifacts

- `08_scripts/lib/smr_human_review_workflow.py`
- `08_scripts/jobs/apply_human_review_action.py`
- `08_scripts/reporting/build_review_queue_snapshot.py`
- `08_scripts/reporting/build_phase15_unknown_thesis_diagnostics.py`
- `08_scripts/reporting/build_phase15_review_ops_summary.py`
- `08_scripts/verification/validate_phase15_review_to_paper_smoke.py`
- `08_scripts/verification/validate_phase15_core_blocker_recovery.py`
- `docs/plans/2026-05-23-phase15-human-review-core-blocker-recovery.md`

### Phase 15 Expected Behavior

- `09988.HK` reduced-size pending appears in review queue with thesis,
  optional warnings, bear-case status, and portfolio projection.
- `approve_paper` is allowed only from `pending_human_review`.
- `reduce_position_size` can only lower or keep the existing suggested
  position size.
- `approved_paper` is the only status eligible for paper order generation.
- Pending, rejected, archived, and needs-more-research items cannot generate
  paper orders.
- Core blocker recovery reports before/after field status, but does not
  fabricate missing fundamentals.
- Unknown-thesis diagnostics suggest metadata patches without changing the
  watchlist automatically.

### Phase 15 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase13_core_gate_repaired_candidate.py --ticker 09988.HK --days 365 --thesis valuation_rerating --json
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_review_queue_snapshot.py --json
python 08_scripts/jobs/apply_human_review_action.py --recommendation-id phase14__09988.HK__valuation_rerating --action approve_paper --reviewer manual --note "phase15 dry-run approval" --dry-run
python 08_scripts/verification/validate_phase15_review_to_paper_smoke.py --ticker 09988.HK --dry-run --json
python 08_scripts/verification/validate_phase15_core_blocker_recovery.py --ticker 00700.HK --json
python 08_scripts/reporting/build_phase15_unknown_thesis_diagnostics.py --ticker 002230.SZ --json
python 08_scripts/reporting/build_phase15_review_ops_summary.py --watchlist ai_core --json
```

## Stage 16 Goal

Phase 16 focuses on parser recovery and thesis metadata hardening. It does not
try to create more pending recommendations. Instead, it turns broad core
blockers into either repaired fields with evidence IDs or precise missing
reasons that can be worked from.

Current Phase 15 checkpoint:

- Commit: `3637f821f160433dd9c2feb34a3459671f40f8f7`
- Stage: `Phase 15: Human Review Workflow + Core Blocker Recovery`
- `09988.HK` review workflow and paper order guard are complete.
- `00700.HK` still has `shareholders_equity` as a core blocker.
- `300308.SZ` and `688041.SH` still have `revenue` / `gross_profit` core
  blockers.
- `002230.SZ` remains `unknown` thesis and cannot enter pending review.

### Phase 16 Goals

1. Add HKEX balance sheet parser recovery for `shareholders_equity`.
2. Add HK equity synonym coverage for owners/shareholders equity.
3. Refine `00700.HK` from broad `table_not_found` to a balance-sheet-specific
   reason when extraction is not possible.
4. Add CNINFO income statement parser recovery for `revenue`,
   `operating_cost`, and `gross_profit`.
5. Support A-share `gross_profit = revenue - operating_cost` derivation with
   linked input evidence IDs.
6. Harden `002230.SZ` unknown-thesis diagnostics with a dry-run metadata patch
   and after-patch simulation.
7. Add a Phase 16 parser/thesis recovery validator and daily parser recovery
   summary.

### Phase 16 Non-goals

- Do not perform real trading.
- Do not auto approve anything.
- Do not create paper orders from pending items.
- Do not expand the `ai_core` watchlist.
- Do not loosen promotion rules.
- Do not let unknown thesis bypass thesis-aware evidence gates.
- Do not use source-missing or low-confidence fields as promotion evidence.

### Phase 16 New Artifacts

- `08_scripts/lib/smr_hkex_table_parser.py`
- `08_scripts/lib/smr_cninfo_table_parser.py`
- `08_scripts/jobs/apply_watchlist_metadata_patch.py`
- `08_scripts/verification/validate_phase16_parser_thesis_recovery.py`
- `08_scripts/reporting/build_phase16_parser_recovery_summary.py`
- `docs/plans/2026-05-23-phase16-parser-thesis-recovery.md`

### Phase 16 Expected Behavior

- `00700.HK` `shareholders_equity` no longer reports only a broad
  `table_not_found`; it is either extracted with source evidence or refined to
  a specific balance-sheet parser reason.
- A-share revenue and gross-profit blockers are either extracted/derived with
  input evidence IDs or refined to income-statement-specific missing reasons.
- `002230.SZ` receives a concrete suggested metadata patch and simulation, but
  remains blocked from pending unless normal thesis inference and evidence gates
  pass later.
- Phase 15 review and paper-order guard behavior remains unchanged.

### Phase 16 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase15_review_ops_summary.py --watchlist ai_core --json
python 08_scripts/verification/validate_phase15_core_blocker_recovery.py --ticker 00700.HK --json
python 08_scripts/verification/validate_phase15_core_blocker_recovery.py --ticker 300308.SZ --json
python 08_scripts/verification/validate_phase15_core_blocker_recovery.py --ticker 688041.SH --json
python 08_scripts/reporting/build_phase15_unknown_thesis_diagnostics.py --ticker 002230.SZ --json
python 08_scripts/verification/validate_phase16_parser_thesis_recovery.py --json
python 08_scripts/reporting/build_phase16_parser_recovery_summary.py --json
python 08_scripts/jobs/apply_watchlist_metadata_patch.py --ticker 002230.SZ --dry-run
```

## Stage 17 Goal

Phase 17 focuses on financial statement source chunk recovery. Phase 16 made
the parser failures more precise, but it also showed that the current evidence
graph did not always contain true financial statement table chunks. Phase 17
therefore recovers the primary report source, extracts the table chunk, links it
back to evidence, and only then reruns the parser.

Current Phase 16 checkpoint:

- Commit: `8eea7d08ad4cd3a8d6b2bbc5a503e7c190f2b73f`
- Stage: `Phase 16: HKEX / CNINFO Parser Recovery + Thesis Metadata Hardening`
- `00700.HK` `shareholders_equity` was refined to `balance_sheet_not_found`.
- `300308.SZ` and `688041.SH` `revenue` / `gross_profit` were refined to
  `income_statement_table_not_found`.
- `002230.SZ` unknown thesis diagnostics improved, but the ticker still does
  not bypass the evidence gate or enter pending review.

### Phase 17 Goals

1. Discover primary HKEX / CNINFO financial statement sources.
2. Extract income statement, balance sheet, and cash flow chunks from reports.
3. Classify financial statement chunks and reject contents, disclaimers, and
   management discussion sections as core statement tables.
4. Link recovered chunks to `document_chunks` and `evidence_items`.
5. Rerun the Phase 16 parsers on recovered chunks.
6. Validate `00700.HK`, `300308.SZ`, and `688041.SH` before/after status.
7. Summarize sources found, chunks found, evidence linked, extracted fields,
   derived fields, and remaining table-not-found blockers.

### Phase 17 Non-goals

- Do not perform real trading.
- Do not auto approve anything.
- Do not generate paper orders or paper positions.
- Do not expand the `ai_core` watchlist.
- Do not loosen promotion rules.
- Do not fabricate extracted fields when no source table chunk exists.
- Do not use source-missing or low-confidence fields as core evidence.
- Do not commit raw PDFs, HTML dumps, or large generated extraction outputs.

### Phase 17 New Artifacts

- `08_scripts/lib/smr_financial_statement_source_discovery.py`
- `08_scripts/lib/smr_financial_statement_chunker.py`
- `08_scripts/jobs/discover_financial_statement_sources.py`
- `08_scripts/jobs/extract_financial_statement_chunks.py`
- `08_scripts/jobs/link_financial_statement_chunks_to_evidence.py`
- `08_scripts/verification/validate_phase17_source_chunk_recovery.py`
- `08_scripts/reporting/build_phase17_source_chunk_recovery_summary.py`
- `00_control/financial_statement_sources.json`
- `docs/plans/2026-05-23-phase17-financial-statement-source-chunk-recovery.md`

### Phase 17 Expected Behavior

- `00700.HK` can discover a HKEX annual report, extract a balance sheet chunk,
  link it to evidence, and rerun `shareholders_equity` extraction.
- `300308.SZ` can discover a CNINFO annual report, extract an income statement
  chunk, link it to evidence, and rerun `revenue` / `gross_profit` extraction.
- `688041.SH` remains acceptable as a refined missing source case if CNINFO
  org hints or manifest source metadata are unavailable.
- The system reports what source and chunk were used, which evidence ID was
  created, and why any remaining field cannot be extracted.

### Phase 17 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase15_review_ops_summary.py --watchlist ai_core --json
python 08_scripts/verification/validate_phase16_parser_thesis_recovery.py --json
python 08_scripts/jobs/discover_financial_statement_sources.py --tickers 00700.HK,300308.SZ,688041.SH --json
python 08_scripts/jobs/extract_financial_statement_chunks.py --tickers 00700.HK,300308.SZ,688041.SH --json
python 08_scripts/jobs/link_financial_statement_chunks_to_evidence.py --ticker 00700.HK --json
python 08_scripts/jobs/link_financial_statement_chunks_to_evidence.py --ticker 300308.SZ --json
python 08_scripts/jobs/link_financial_statement_chunks_to_evidence.py --ticker 688041.SH --json
python 08_scripts/verification/validate_phase17_source_chunk_recovery.py --tickers 00700.HK,300308.SZ,688041.SH --json
python 08_scripts/reporting/build_phase17_source_chunk_recovery_summary.py --json
```

## Stage 18 Goal

Phase 18 closes the remaining source gap and moves recovered financial
statement fields into the system path that matters: fundamentals snapshots and
the thesis-aware core blocker gate. It does not create more aggressive
promotion behavior.

Current Phase 17 checkpoint:

- Commit: `050a0e9b69708ee83197e84d55f557f858fc2b2f`
- Stage: `Phase 17: Financial Statement Source Chunk Recovery`
- `00700.HK` `shareholders_equity` is extracted from HKEX financial statement
  evidence.
- `300308.SZ` `revenue` is extracted and `gross_profit` is derived from CNINFO
  income statement evidence.
- `688041.SH` was still `financial_statement_source_not_found`.
- No new pending review, no promotion relaxation, and no trading action were
  introduced.

### Phase 18 Goals

1. Resolve `688041.SH` CNINFO source identity.
2. Discover and cache a usable `688041.SH` annual report source.
3. Extract and link `688041.SH` income statement chunks.
4. Recover `688041.SH` `revenue` and `gross_profit` when evidence is present.
5. Insert recovered `00700.HK`, `300308.SZ`, and `688041.SH` fields into new
   fundamentals snapshots with lineage.
6. Let thesis-aware core blocker logic remove recovered fields only when the
   snapshot has evidence IDs and sufficient confidence.
7. Add Phase 18 revalidation and a daily fundamentals recovery summary.

### Phase 18 Non-goals

- Do not perform real trading.
- Do not auto approve anything.
- Do not generate paper orders or paper positions.
- Do not expand `ai_core`.
- Do not loosen promotion rules.
- Do not fabricate fields without source chunks and evidence IDs.
- Do not allow low-confidence recovered fields to clear core blockers.
- Do not commit raw PDF, HTML, or generated report outputs.

### Phase 18 New Artifacts

- `08_scripts/lib/smr_cninfo_source_identity.py`
- `08_scripts/lib/smr_recovered_fundamentals.py`
- `08_scripts/jobs/resolve_cninfo_source_identity.py`
- `08_scripts/jobs/update_fundamentals_from_recovered_chunks.py`
- `08_scripts/verification/validate_phase18_remaining_source_gap_closure.py`
- `08_scripts/verification/validate_phase18_fundamentals_recovery_revalidation.py`
- `08_scripts/reporting/build_phase18_fundamentals_recovery_summary.py`
- `docs/plans/2026-05-23-phase18-fundamentals-recovery-expansion.md`

### Phase 18 Expected Behavior

- `688041.SH` resolves to a CNINFO identity and source manifest entry.
- `688041.SH` discovers the 2025 annual report and extracts financial statement
  chunks.
- `688041.SH` `revenue` and `gross_profit` can be recovered from linked income
  statement evidence.
- `00700.HK`, `300308.SZ`, and `688041.SH` recovered fields are represented in
  fundamentals snapshots with previous-value metadata.
- Phase 14 missing-field logic treats recovered, traceable fields as no longer
  missing, while low-confidence/context-only fields remain blocking.

### Phase 18 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase15_review_ops_summary.py --watchlist ai_core --json
python 08_scripts/verification/validate_phase16_parser_thesis_recovery.py --json
python 08_scripts/verification/validate_phase17_source_chunk_recovery.py --tickers 00700.HK,300308.SZ,688041.SH --json
python 08_scripts/jobs/resolve_cninfo_source_identity.py --ticker 688041.SH --json
python 08_scripts/jobs/discover_financial_statement_sources.py --ticker 688041.SH --json
python 08_scripts/jobs/extract_financial_statement_chunks.py --ticker 688041.SH --json
python 08_scripts/jobs/link_financial_statement_chunks_to_evidence.py --ticker 688041.SH --json
python 08_scripts/verification/validate_phase18_remaining_source_gap_closure.py --ticker 688041.SH --json
python 08_scripts/jobs/update_fundamentals_from_recovered_chunks.py --tickers 00700.HK,300308.SZ,688041.SH --json
python 08_scripts/verification/validate_phase18_fundamentals_recovery_revalidation.py --tickers 00700.HK,300308.SZ,688041.SH --json
python 08_scripts/reporting/build_phase18_fundamentals_recovery_summary.py --json
```

## Stage 19 Goal

Phase 19 explains the higher-level gates that remain after Phase 18 cleared
the recovered fundamentals blockers. It does not create a more aggressive
promotion path; it makes the remaining conservatism visible and actionable.

Current Phase 18 checkpoint:

- Commit: `5aeebb9df7f66f470432b2143a10b0b7493af150`
- Stage: `Phase 18: Remaining Source Gap Closure + Fundamentals Recovery Expansion`
- `00700.HK` `shareholders_equity` is in the fundamentals snapshot.
- `300308.SZ` `revenue` and `gross_profit` are in the fundamentals snapshot.
- `688041.SH` CNINFO identity, source, chunks, evidence, `revenue`, and
  `gross_profit` are recovered and in the fundamentals snapshot.
- Core blockers were reduced to zero for `00700.HK`, `300308.SZ`, and
  `688041.SH`.
- No new pending review, no promotion relaxation, and no trading action were
  introduced.

### Phase 19 Goals

1. Add a promotion block reason hierarchy.
2. Diagnose filing freshness and evidence freshness.
3. Add evidence quality gate v2 diagnostics.
4. Decompose bear case residual risk.
5. Explain the `002230.SZ` thesis evidence gate.
6. Validate the promotion impact of recovered fundamentals.
7. Build a daily gate summary with remaining gate distribution.

### Phase 19 Non-goals

- Do not perform real trading.
- Do not auto approve anything.
- Do not generate paper orders or paper positions.
- Do not expand `ai_core`.
- Do not loosen promotion rules.
- Do not delete bear cases.
- Do not upgrade `partially_mitigated` to `mitigated` without evidence.
- Do not allow metadata-only unknown thesis recovery to create pending review.

### Phase 19 New Artifacts

- `08_scripts/lib/smr_promotion_block_reason.py`
- `08_scripts/lib/smr_filing_freshness.py`
- `08_scripts/reporting/build_phase19_promotion_block_diagnostics.py`
- `08_scripts/reporting/build_phase19_filing_freshness_diagnostics.py`
- `08_scripts/reporting/build_phase19_evidence_quality_gate_summary.py`
- `08_scripts/reporting/build_phase19_bear_case_residual_risk.py`
- `08_scripts/reporting/build_phase19_thesis_evidence_gate.py`
- `08_scripts/verification/validate_phase19_recovered_fundamentals_promotion_impact.py`
- `08_scripts/reporting/build_phase19_daily_gate_summary.py`
- `docs/plans/2026-05-23-phase19-noncore-gate-resolution.md`

### Phase 19 Expected Behavior

- Every `ai_core` ticker has one `primary_blocking_gate`.
- Tickers with empty core blockers are not misreported as core fundamentals
  blockers.
- Filing freshness can block pending review when stale or missing.
- Evidence quality is ranked as high, medium, low, or blocked.
- Bear case residual risk explains whether reduced-size pending is allowed.
- `002230.SZ` can show high metadata simulation confidence while still
  remaining blocked by missing thesis evidence.
- Daily summary shows gate distribution, recovered fields, and next fixes.

### Phase 19 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase15_review_ops_summary.py --watchlist ai_core --json
python 08_scripts/verification/validate_phase18_fundamentals_recovery_revalidation.py --tickers 00700.HK,300308.SZ,688041.SH --json
python 08_scripts/reporting/build_phase19_promotion_block_diagnostics.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase19_filing_freshness_diagnostics.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase19_evidence_quality_gate_summary.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase19_bear_case_residual_risk.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase19_thesis_evidence_gate.py --ticker 002230.SZ --json
python 08_scripts/verification/validate_phase19_recovered_fundamentals_promotion_impact.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase19_daily_gate_summary.py --watchlist ai_core --json
```
