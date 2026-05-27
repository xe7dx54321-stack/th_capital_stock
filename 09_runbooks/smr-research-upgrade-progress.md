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

## Phase 31: Evidence Candidate Review Queue + Manual Evidence Governance v1

Phase 31 productizes semantic evidence governance after Phase 30 persistence.
The phase adds a review queue, lifecycle states, manual governance actions,
append-only audit logs, download repair tasks, sensitive-variable guardrails,
variable-pack link audit, and governance revalidation.

Phase 30 checkpoint:

- Persisted semantic evidence candidates: `60`
- Review-required candidates: `1`
- Rejected/noisy candidate cleanup: completed in Phase 30
- Download-unavailable sources: `2`
- `usable_for_promotion_true=0`
- `confirmed_variables_added=0`
- `new_pending_created=0`

### Phase 31 Goals

1. Add evidence lifecycle schema.
2. Add evidence review queue for pending, weak, sensitive, rejected, removed,
   and repair items.
3. Add manual evidence review actions with safety guards.
4. Add evidence review audit log.
5. Add evidence governance dashboard.
6. Add download-unavailable repair queue.
7. Add sensitive variable guard.
8. Add variable pack link audit.
9. Add governance revalidation.

### Phase 31 Guardrails

- Persisted candidate is not automatically approved evidence.
- Approved evidence is not promotion evidence.
- Manual review actions cannot enable `usable_for_promotion`.
- Manual review actions cannot create confirmed supplier share, confirmed ASP,
  confirmed customer allocation, official consensus, pending review, paper
  orders, paper positions, or real trades.
- Rejected, marked-noise, removed, and archived evidence remains auditable.
- Download repair tasks do not bypass download controls and do not enable OCR by
  default.
- Raw PDF, raw HTML, text cache, DB, and log files are not committed.

### Phase 31 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase30_semantic_evidence_hardening_summary.py --json
python 08_scripts/reporting/build_phase31_evidence_review_queue.py --json
python 08_scripts/jobs/apply_evidence_review_action.py --evidence-id <EXISTING_EVIDENCE_ID> --action approve_evidence --dry-run --json
python 08_scripts/jobs/apply_evidence_review_action.py --evidence-id <EXISTING_EVIDENCE_ID> --action downgrade_usage --target-usage context_only --dry-run --json
python 08_scripts/reporting/build_phase31_evidence_review_audit_report.py --json
python 08_scripts/reporting/build_phase31_evidence_governance_dashboard.py --json
python 08_scripts/jobs/upsert_download_unavailable_repair_tasks.py --dry-run --json
python 08_scripts/reporting/build_phase31_download_repair_queue_summary.py --json
python 08_scripts/verification/validate_phase31_sensitive_variable_guard.py --json
python 08_scripts/reporting/build_phase31_variable_pack_link_audit.py --json
python 08_scripts/verification/validate_phase31_evidence_governance_revalidation.py --json
```

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

## Stage 20 Goal

Phase 20 starts addressing the higher-level research gates identified by
Phase 19. It is still a conservative diagnostic and evidence-mapping phase:
it does not loosen promotion rules, auto approve reviews, or create real
trading actions.

Current Phase 19 checkpoint:

- Commit: `72cb4f08818127226b87d52408b14e8c53ad7228`
- Stage: `Phase 19: Non-core Gate Resolution + Evidence Freshness & Bear Case Mitigation`
- Core blockers are cleared.
- Filing freshness is fresh for `ai_core`.
- Evidence quality has no blocked evidence.
- Remaining gates include `BEAR_CASE_GATE`, `VALUATION_GATE`,
  `REVIEW_STATE_GATE`, and `THESIS_CONFIDENCE_GATE`.
- `002230.SZ` has high metadata-simulated thesis confidence but lacks enough
  claim graph, proxy, and filing/news support for pending review.

### Phase 20 Goals

1. Map bear cases to mitigating evidence.
2. Split valuation blockers into actionable codes.
3. Strengthen internal proxy signal diagnostics without calling them official
   consensus.
4. Build an evidence pack for the `002230.SZ` thesis candidate.
5. Revalidate promotion impact after gate diagnostics.
6. Build a daily research gate summary.

### Phase 20 Non-goals

- Do not perform real trading.
- Do not auto approve pending review.
- Do not generate paper orders or paper positions.
- Do not expand `ai_core`.
- Do not loosen promotion rules.
- Do not delete or hide bear cases.
- Do not use weak evidence to mitigate core bear cases.
- Do not let metadata-only thesis inference create pending review.
- Do not treat proxy EPS or internal proxy signals as official consensus.

### Phase 20 New Artifacts

- `08_scripts/lib/smr_bear_case_mitigation.py`
- `08_scripts/lib/smr_valuation_gate.py`
- `08_scripts/lib/smr_proxy_signal_gate.py`
- `08_scripts/reporting/build_phase20_bear_case_mitigation.py`
- `08_scripts/reporting/build_phase20_valuation_gate_diagnostics.py`
- `08_scripts/reporting/build_phase20_proxy_signal_gate.py`
- `08_scripts/reporting/build_phase20_002230_thesis_evidence_pack.py`
- `08_scripts/verification/validate_phase20_promotion_revalidation.py`
- `08_scripts/reporting/build_phase20_research_gate_summary.py`
- `docs/plans/2026-05-23-phase20-bear-valuation-proxy-gate.md`

### Phase 20 Expected Behavior

- Bear case mitigation outputs evidence ids or explicit missing evidence.
- Financial statement evidence may mitigate revenue, margin, valuation, or
  data-quality risk.
- Financial statement evidence does not directly mitigate order, direct demand,
  competitive, policy, or thesis-confidence risk.
- Valuation diagnostics show concrete blocker codes.
- Proxy diagnostics show direction, strength, independent source count,
  evidence quality, thesis alignment, and conflicts.
- `002230.SZ` can be upgraded from metadata-only to evidence-backed thesis
  candidate only when non-metadata evidence exists.
- Pending review is not required; if it ever appears, it must be reduced-size,
  require human review, and disallow paper orders.

### Phase 20 Validation Commands

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

## Stage 21 Goal

Phase 21 converts the Phase 20 missing direct-demand and independent-proxy
evidence blockers into structured, auditable, re-runnable diagnostics. It is
still not a new industry-chain agent and still does not loosen promotion rules.

Current Phase 20 checkpoint:

- Commit: `5d5b1a8fdd8bd127df9186a6959d1ae4812303f5`
- Stage: `Phase 20: Bear Case Evidence Mitigation + Valuation/Proxy Gate Strengthening`
- Bear case, valuation, proxy, and thesis evidence gates are explainable.
- `300308.SZ`, `688041.SH`, and `002230.SZ` still need direct demand, order,
  customer, capex, or independent source evidence.
- `002230.SZ` is an evidence-backed thesis candidate but still lacks dominant
  proxy signal and enough independent source support.
- No promotion rules were relaxed and no real trading risk was introduced.

### Phase 21 Goals

1. Build a direct demand evidence schema.
2. Extract demand/order/customer/capex evidence from existing local evidence.
3. Expand internal proxy source counts using eligible direct demand evidence.
4. Convert missing bear-case evidence into repair queue tasks.
5. Re-run bear-case mitigation with demand evidence.
6. Revalidate promotion impact.
7. Build a demand/proxy gate summary.

### Phase 21 Non-goals

- Do not add a full industry-chain agent.
- Do not perform real trading.
- Do not auto approve pending review.
- Do not generate paper orders or paper positions.
- Do not expand `ai_core`.
- Do not loosen promotion rules.
- Do not treat weak evidence as strong evidence.
- Do not treat news rumors as customer order confirmation.
- Do not treat management commentary as confirmed order.
- Do not treat internal proxy as official consensus.
- Do not commit raw/PDF/HTML source files.

### Phase 21 New Artifacts

- `08_scripts/lib/smr_direct_demand_evidence.py`
- `08_scripts/jobs/build_direct_demand_evidence.py`
- `08_scripts/reporting/build_phase21_direct_demand_evidence_summary.py`
- `08_scripts/reporting/build_phase21_proxy_source_expansion.py`
- `08_scripts/jobs/upsert_bear_case_evidence_repair_tasks.py`
- `08_scripts/verification/validate_phase21_bear_case_demand_mitigation.py`
- `08_scripts/verification/validate_phase21_promotion_revalidation.py`
- `08_scripts/reporting/build_phase21_demand_proxy_gate_summary.py`
- `docs/plans/2026-05-23-phase21-demand-proxy-expansion.md`

### Phase 21 Expected Behavior

- Demand evidence requires `evidence_id` and `independent_source_key`.
- Management commentary can support a gate but is not a confirmed order.
- Rumor or unconfirmed evidence is blocked or context-only.
- Metadata does not count as an independent proxy source.
- Demand evidence can improve bear-case or proxy diagnostics, but cannot
  directly create pending review.
- If pending review ever appears, it must be reduced-size, require human
  review, and keep `paper_order_allowed=false`.

### Phase 21 Validation Commands

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

## Stage 22 Goal

Phase 22 upgrades the largest remaining post-Phase-21 gate: valuation. It also
escalates demand evidence from broad indications into explicit confirmed-order,
tender/procurement, customer-capex, management-guidance, and industry-context
categories.

Current Phase 21 checkpoint:

- Commit: `1981508dc551098bc080e33ca130f0b0750bdddc`
- Stage: `Phase 21: Direct Demand Evidence + Independent Proxy Source Expansion`
- Direct demand evidence is available for `300308.SZ`, `688041.SH`, and
  `002230.SZ`.
- `300308.SZ` and `688041.SH` bear cases are partially mitigated.
- Proxy sources expanded, but `002230.SZ` remains weak.
- Remaining gates include `VALUATION_GATE`, `PROXY_SIGNAL_GATE`, and
  `BEAR_CASE_GATE`.
- No new pending review, no promotion-rule relaxation, and no real trading risk
  were introduced.

### Phase 22 Goals

1. Add valuation gate v2 with concrete blocker codes.
2. Link direct demand evidence to valuation assumptions.
3. Escalate demand evidence into confirmed/tender/customer-capex categories.
4. Strengthen internal proxy source diagnostics.
5. Revalidate promotion impact across valuation, demand, proxy, and bear-case
   gates.
6. Build a valuation/demand gate summary.
7. Convert remaining valuation, demand, and proxy gaps into repair queue tasks.

### Phase 22 Non-goals

- Do not add a full industry-chain agent.
- Do not perform real trading.
- Do not auto approve pending review.
- Do not generate paper orders or paper positions.
- Do not expand `ai_core`.
- Do not loosen promotion rules.
- Do not treat indication as confirmed order.
- Do not treat management commentary as customer order.
- Do not treat internal proxy or proxy EPS as official consensus.
- Do not commit raw/PDF/HTML source files.

### Phase 22 New Artifacts

- `08_scripts/lib/smr_demand_valuation_linkage.py`
- `08_scripts/lib/smr_valuation_gate_v2.py`
- `08_scripts/reporting/build_phase22_valuation_gate_upgrade.py`
- `08_scripts/reporting/build_phase22_demand_valuation_linkage.py`
- `08_scripts/reporting/build_phase22_confirmed_demand_evidence.py`
- `08_scripts/reporting/build_phase22_proxy_strengthening.py`
- `08_scripts/verification/validate_phase22_valuation_demand_promotion_revalidation.py`
- `08_scripts/reporting/build_phase22_valuation_demand_gate_summary.py`
- `08_scripts/jobs/upsert_phase22_valuation_demand_repair_tasks.py`
- `docs/plans/2026-05-23-phase22-valuation-demand-gate-upgrade.md`

### Phase 22 Expected Behavior

- Valuation diagnostics expose exact blocker codes and next fixes.
- Demand evidence can support revenue-growth assumptions, but cannot replace
  valuation models.
- Signed contract, tender, and procurement evidence can provide strong support.
- Management commentary remains medium support at most.
- Customer capex is a strong indication, not a confirmed company order.
- Proxy EPS remains internal/supporting and is not official consensus.
- Reduced-size pending remains human-review only and is not automatically
  created by diagnostics.

### Phase 22 Validation Commands

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

## Stage 23 Goal

Phase 23 adds a source routing layer. The system already knows which valuation,
demand, proxy, and bear-case gates are missing evidence; this stage makes the
next step explicit by mapping each blocker to information types, source routes,
connector status, fallback sources, and acquisition plans.

Current Phase 22 checkpoint:

- Commit: `28eea04746eeafd7fab01b12ca8448e6eeae07e2`
- Stage: `Phase 22: Valuation Gate Upgrade + Confirmed Demand Evidence Escalation`
- `VALUATION_GATE` is the largest remaining gate.
- `confirmed_order_count=0`.
- `tender_or_procurement_count=0`.
- `customer_capex_count=3`.
- Phase 22 repair task dry-run identified `35` tasks.
- No new pending review, no full-size pending, no promotion-rule relaxation, and
  no real trading risk were introduced.

### Phase 23 Goals

1. Add Source Connector Registry v2.
2. Add blocker-to-information-type routing.
3. Route valuation blockers to source connectors.
4. Route demand, order, tender, procurement, customer-capex, and proxy blockers.
5. Generate repair task source acquisition plans.
6. Build connector availability dashboard.
7. Validate source route coverage without changing promotion outcomes.

### Phase 23 Non-goals

- Do not add a full industry-chain agent.
- Do not add an investment committee agent.
- Do not perform real trading.
- Do not expand `ai_core`.
- Do not add large raw source files.
- Do not loosen promotion rules.
- Do not treat planned connectors as implemented connectors.
- Do not treat unavailable sources as usable evidence.
- Do not treat commercial consensus as implemented.
- Do not treat internal proxy as official consensus.
- Do not auto approve pending review.
- Do not create paper orders or paper positions.

### Phase 23 New Artifacts

- `00_control/source_connector_registry_v2.json`
- `00_control/blocker_source_route_map.json`
- `08_scripts/lib/smr_source_connector_registry.py`
- `08_scripts/lib/smr_blocker_source_router.py`
- `08_scripts/lib/smr_source_acquisition_plan.py`
- `08_scripts/reporting/build_phase23_source_connector_registry_report.py`
- `08_scripts/reporting/build_phase23_valuation_source_routing.py`
- `08_scripts/reporting/build_phase23_demand_source_routing.py`
- `08_scripts/reporting/build_phase23_source_acquisition_plan.py`
- `08_scripts/reporting/build_phase23_connector_availability_dashboard.py`
- `08_scripts/verification/validate_phase23_source_routing_revalidation.py`
- `docs/plans/2026-05-23-phase23-source-connector-registry-v2.md`

### Phase 23 Expected Behavior

- Planned connectors appear as future actions only.
- `official_consensus` remains `planned_only`.
- Internal proxy remains supporting evidence and is not official consensus.
- Tender/procurement connectors remain planned unless explicitly implemented.
- Source acquisition plans do not fetch data or write evidence graph entries.
- Promotion status should not change because Phase 23 is routing-only.

### Phase 23 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase22_valuation_demand_gate_summary.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase23_source_connector_registry_report.py --json
python 08_scripts/reporting/build_phase23_valuation_source_routing.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase23_demand_source_routing.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase23_source_acquisition_plan.py --tickers 300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase23_connector_availability_dashboard.py --json
python 08_scripts/verification/validate_phase23_source_routing_revalidation.py --watchlist ai_core --json
```

## Stage 24 Goal

Phase 24 turns the Phase 23 planned `cn_tender_procurement` route into a
conservative executable connector. The focus is not broad web crawling; it is a
small, auditable chain for CN tender, procurement, award, contract, and customer
project evidence that can be normalized and linked into direct demand gates.

Current Phase 23 checkpoint:

- Commit: `9d420054d6f91677688f8e8420fc1e241f81fbe9`
- Stage: `Phase 23: Source Connector Registry v2 + Valuation Source Routing`
- Source routing can explain where to look for missing evidence.
- `cn_tender_procurement` was still planned.
- Confirmed order, tender, and procurement evidence remained key demand gaps.
- Phase 23 created no pending review, no paper order, and no promotion-rule
  relaxation.

### Phase 24 Goals

1. Add CN tender/procurement source schema.
2. Add deterministic query planner for `300308.SZ`, `688041.SH`, and
   `002230.SZ`.
3. Add executable `cn_tender_procurement` connector v1.
4. Normalize tender, procurement, award, contract, customer capex, and news
   mentions into evidence candidates.
5. Link normalized items into evidence graph candidates only when `source_url`
   is present.
6. Feed tender evidence into direct demand evidence summaries.
7. Revalidate proxy, bear-case, and promotion impact without auto pending.
8. Update registry status conservatively to `partial`.
9. Build Phase 24 tender/procurement summary reports.

### Phase 24 Non-goals

- Do not add a full industry-chain agent.
- Do not perform real trading.
- Do not expand `ai_core`.
- Do not crawl or commit raw HTML, PDF, or log files.
- Do not treat tender notices as tender awards.
- Do not treat procurement notices or purchase intentions as confirmed orders.
- Do not treat news reposts as official award evidence.
- Do not loosen promotion rules or auto approve pending review.

### Phase 24 New Artifacts

- `08_scripts/lib/smr_cn_tender_procurement.py`
- `08_scripts/lib/smr_cn_tender_query_planner.py`
- `08_scripts/lib/smr_tender_evidence_linkage.py`
- `08_scripts/jobs/fetch_cn_tender_procurement.py`
- `08_scripts/reporting/build_phase24_cn_tender_procurement_summary.py`
- `08_scripts/reporting/build_phase24_tender_procurement_summary.py`
- `08_scripts/verification/validate_phase24_tender_procurement_revalidation.py`
- `docs/plans/2026-05-23-phase24-cn-tender-procurement-connector.md`

### Phase 24 Expected Behavior

- `cn_tender_procurement` is `partial`, not `implemented`.
- Dry-run produces queries and normalized candidates but writes no evidence
  graph rows.
- Execute mode writes only normalized evidence candidates with `source_url`.
- Tender/procurement evidence can support direct demand and proxy/bear-case
  diagnostics.
- Tender notices remain indications and cannot trigger pending.
- Promotion status is reported, not automatically changed.

### Phase 24 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase23_connector_availability_dashboard.py --json
python 08_scripts/jobs/fetch_cn_tender_procurement.py --tickers 300308.SZ,688041.SH,002230.SZ --dry-run --json
python 08_scripts/reporting/build_phase24_cn_tender_procurement_summary.py --tickers 300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/verification/validate_phase24_tender_procurement_revalidation.py --tickers 300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase24_tender_procurement_summary.py --watchlist ai_core --json
```

## Phase 25: Supply Chain Expectation Gap Engine v1

Phase 25 moves the research stack from "find tender/order evidence" toward a
scenario-based supply-chain expectation gap framework. The point is not to
discover unavailable customer allocation or supplier-share data. The point is to
make the assumptions explicit, score the gap conservatively, and route the next
missing variables to the right future connectors.

Current Phase 24 checkpoint:

- Commit: `f6f516867b5714c530407b3ade595d458d01f2ce`
- Stage: `Phase 24: CN Tender / Procurement Connector v1`
- `cn_tender_procurement` moved from planned to partial.
- Dry-run works for `300308.SZ`, `688041.SH`, and `002230.SZ`.
- Target tickers generated `queries=72`.
- `raw_results_found=1`, `normalized_items=1`, `evidence_candidates=1`.
- `confirmed_awards=0`; no indication was promoted into a confirmed order.
- No pending review was created, no paper order was created, and no promotion
  rule was relaxed.

### Phase 25 Goals

1. Add supply-chain theme template support.
2. Add supplier exposure profiles for the pilot tickers.
3. Add `300394.SZ` through a separate `supply_chain_pilot` watchlist instead of
   expanding `ai_core`.
4. Build end-demand proxy output for `ai_optical_interconnect`.
5. Build scenario-only revenue sensitivity output.
6. Build expectation gap scoring with uncertainty penalties.
7. Build expectation gap packets for research review.
8. Validate thesis, valuation, and bear-case gate impact without allowing gap-only
   promotion.
9. Build a Phase 25 summary dashboard.

### Phase 25 Guardrails

- Do not build a full tender/procurement platform expansion.
- Do not add an industry-chain agent or investment committee agent.
- Do not use paid commercial data sources.
- Do not fabricate NVIDIA, hyperscaler, customer order, supplier-share, ASP, or
  customer allocation data.
- Do not treat industry forecasts as company orders.
- Do not treat internal proxy estimates as official consensus.
- Do not loosen promotion rules.
- Do not create pending review, paper orders, paper positions, or real trading
  actions from expectation gap alone.
- Do not commit raw HTML, PDF, or large log files.

### Phase 25 New Artifacts

- `00_control/supply_chain_theme_templates.json`
- `00_control/supplier_exposure_profiles.json`
- `00_control/watchlists/supply_chain_pilot.json`
- `08_scripts/lib/smr_supply_chain_theme_template.py`
- `08_scripts/lib/smr_supplier_exposure_model.py`
- `08_scripts/lib/smr_end_demand_proxy.py`
- `08_scripts/lib/smr_revenue_sensitivity_model.py`
- `08_scripts/lib/smr_expectation_gap.py`
- `08_scripts/reporting/build_phase25_end_demand_proxy.py`
- `08_scripts/reporting/build_phase25_revenue_sensitivity.py`
- `08_scripts/reporting/build_phase25_expectation_gap.py`
- `08_scripts/reporting/build_phase25_supply_chain_expectation_gap_packet.py`
- `08_scripts/reporting/build_phase25_supply_chain_gap_summary.py`
- `08_scripts/verification/validate_phase25_expectation_gap_gate_integration.py`
- `docs/plans/2026-05-23-phase25-supply-chain-expectation-gap.md`

### Phase 25 Expected Behavior

- `ai_optical_interconnect` end-demand proxy can output direction, confidence,
  active evidence, planned sources, and limitations.
- Supplier profiles remain `scenario_analysis_only`.
- `300394.SZ` is available in the pilot watchlist, not added to `ai_core`.
- Revenue sensitivity can emit scenario cases with missing variables instead of
  forcing precise revenue estimates.
- Expectation gap can identify low-confidence positive candidates while applying
  uncertainty penalties.
- Expectation gap packets default to `promotion_allowed=false`.
- Gate integration reports thesis and valuation support impact but never creates
  pending review from expectation gap alone.

### Phase 25 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase24_tender_procurement_summary.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase25_end_demand_proxy.py --theme ai_optical_interconnect --json
python 08_scripts/reporting/build_phase25_revenue_sensitivity.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase25_expectation_gap.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase25_supply_chain_expectation_gap_packet.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/verification/validate_phase25_expectation_gap_gate_integration.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase25_supply_chain_gap_summary.py --json
```

## Phase 26: Supply Chain Variable Evidence Connector v1

Phase 26 adds auditable evidence packs for the most important variables inside
the supply-chain expectation gap engine. The goal is not to add another
reasoning layer. The goal is to show, variable by variable, whether evidence
exists, what source route is available, what confidence is justified, and what
connector should be added next.

Current Phase 25 checkpoint:

- Commit: `10313d33b34e134d8db68f742f820ca6b4201039`
- Stage: `Phase 25: Supply Chain Expectation Gap Engine v1`
- `positive_gap_candidates=2`.
- `packets=4`.
- `needs_more_data=4`.
- `promotion_allowed=0`.
- Main bottlenecks are supplier share, ASP, capacity/shipment, customer
  allocation, official consensus, and industry forecast source coverage.

### Phase 26 Goals

1. Add supply-chain variable evidence schema.
2. Add supplier share evidence pack.
3. Add ASP / price proxy evidence pack.
4. Add capacity / shipment evidence pack.
5. Add customer allocation proxy pack.
6. Add consensus / expectation proxy pack.
7. Add industry forecast source routing.
8. Feed variable evidence status back into expectation gap confidence checks.
9. Build a variable evidence summary dashboard.

### Phase 26 Guardrails

- Do not fabricate supplier share.
- Do not fabricate ASP or product price.
- Do not fabricate NVIDIA, hyperscaler, or customer allocation exposure.
- Do not treat customer capex as company revenue.
- Do not treat internal consensus proxy as official consensus.
- Do not treat planned industry forecast sources as active evidence.
- Do not create pending review from expectation gap or variable evidence alone.
- Do not loosen promotion rules.
- Do not create paper orders, paper positions, or real trading actions.
- Do not commit raw HTML, PDF, or large log files.

### Phase 26 New Artifacts

- `08_scripts/lib/smr_supply_chain_variable_evidence.py`
- `08_scripts/reporting/build_phase26_supplier_share_evidence.py`
- `08_scripts/reporting/build_phase26_asp_price_proxy.py`
- `08_scripts/reporting/build_phase26_capacity_shipment_evidence.py`
- `08_scripts/reporting/build_phase26_customer_allocation_proxy.py`
- `08_scripts/reporting/build_phase26_consensus_expectation_proxy.py`
- `08_scripts/reporting/build_phase26_industry_forecast_source_routing.py`
- `08_scripts/verification/validate_phase26_variable_evidence_expectation_gap.py`
- `08_scripts/reporting/build_phase26_variable_evidence_summary.py`
- `docs/plans/2026-05-23-phase26-supply-chain-variable-evidence.md`

### Phase 26 Expected Behavior

- Supplier share packs can show product exposure and missing share disclosure, but
  do not output a fixed share.
- ASP packs can show product mix or price context, but do not output a fabricated
  ASP.
- Capacity packs distinguish capacity expansion from shipment.
- Customer allocation packs keep confirmed allocation false unless direct
  disclosure exists.
- Consensus packs keep official consensus unavailable unless a real authorized
  source is implemented.
- Industry forecast routing keeps commercial or authorized providers as planned
  until implemented.
- Expectation gap confidence can use variable evidence status, but cannot become
  high while supplier share, ASP, customer allocation, or official consensus are
  still missing.

### Phase 26 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase25_supply_chain_gap_summary.py --json
python 08_scripts/reporting/build_phase26_supplier_share_evidence.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase26_asp_price_proxy.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase26_capacity_shipment_evidence.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase26_customer_allocation_proxy.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase26_consensus_expectation_proxy.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase26_industry_forecast_source_routing.py --theme ai_optical_interconnect --json
python 08_scripts/verification/validate_phase26_variable_evidence_expectation_gap.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase26_variable_evidence_summary.py --json
```

## Phase 27: Semantic IR & Industry Forecast Evidence Extractor v1

Phase 27 adds a semantic extraction layer for company IR and public industry
materials. The goal is to move beyond keyword matching while staying fully
auditable: keywords and metadata can recall candidate chunks, but structured
evidence must come from a quoted span and pass a deterministic rule gate before
it can support variable evidence packs.

Current Phase 26 checkpoint:

- Commit: `9295c546dc283a6a1579680be4043685cf9f637d`
- Stage: `Phase 26: Supply Chain Variable Evidence Connector v1`
- Variable evidence packs exist for supplier share, ASP / price proxy, capacity
  / shipment, customer allocation, consensus / expectation, and industry source
  routing.
- Main bottlenecks remain supplier share, ASP, customer allocation, official
  consensus, and higher-quality company IR / industry evidence.
- Phase 26 generated variable evidence packs without creating pending review,
  relaxing promotion rules, or creating trading risk.

### Phase 27 Goals

1. Add semantic evidence extraction schema.
2. Add company IR source inventory.
3. Add IR / industry document chunker.
4. Add candidate retriever for recall only.
5. Add mock-first semantic extractor with reserved `--llm` interface.
6. Add deterministic semantic evidence rule gate.
7. Integrate passed semantic evidence into Phase 26 variable evidence packs.
8. Add public industry forecast semantic extraction.
9. Validate expectation gap, valuation, and bear case gate impact.
10. Add Phase 27 semantic evidence summary dashboard.

### Phase 27 Guardrails

- Do not use keywords as final evidence judgement.
- Do not allow LLM output that is not grounded in the input chunk.
- Do not fabricate customer names, supplier share, ASP, shipment, or customer
  allocation.
- Do not rewrite North American customer as NVIDIA.
- Do not rewrite strong demand as confirmed order.
- Do not rewrite product mix optimization as ASP increase unless the source text
  explicitly says so.
- Do not treat industry forecast as a company-specific order.
- Do not treat internal proxy as official consensus.
- Do not create pending review from semantic evidence alone.
- Do not loosen promotion rules.
- Do not create paper orders, paper positions, or real trading actions.
- Do not commit raw HTML, PDF, or large log files.

### Phase 27 New Artifacts

- `08_scripts/lib/smr_semantic_evidence_schema.py`
- `08_scripts/lib/smr_ir_source_inventory.py`
- `08_scripts/lib/smr_semantic_document_chunker.py`
- `08_scripts/lib/smr_semantic_candidate_retriever.py`
- `08_scripts/lib/smr_ir_semantic_extractor.py`
- `08_scripts/lib/smr_semantic_evidence_gate.py`
- `08_scripts/lib/smr_industry_forecast_semantic_extractor.py`
- `08_scripts/lib/smr_phase27_semantic_pipeline.py`
- `08_scripts/jobs/build_semantic_ir_evidence.py`
- `08_scripts/reporting/build_phase27_ir_source_inventory.py`
- `08_scripts/reporting/build_phase27_industry_forecast_evidence.py`
- `08_scripts/reporting/build_phase27_semantic_evidence_summary.py`
- `08_scripts/verification/validate_phase27_semantic_variable_pack_integration.py`
- `08_scripts/verification/validate_phase27_semantic_evidence_gate_impact.py`
- `docs/plans/2026-05-23-phase27-semantic-ir-industry-forecast-extractor.md`

### Phase 27 Expected Behavior

- IR source inventory can list available or mock-accessible source candidates by
  ticker and source type.
- Document chunker preserves source metadata and keeps Q&A context together.
- Candidate retriever returns candidate chunks and hints only; it does not output
  final variable evidence status.
- Mock semantic extractor is deterministic and default. Reserved `--llm` mode is
  disabled unless explicitly requested and does not run in validation.
- Every extraction must include source id, chunk id, and quoted span.
- Rule gate downgrades management commentary, blocks invalid extractions, and
  keeps promotion disabled.
- Semantic evidence can improve partial/proxy variable evidence, but cannot add
  confirmed supplier share, confirmed customer allocation, official consensus, or
  confirmed orders by itself.

### Phase 27 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase26_variable_evidence_summary.py --json
python 08_scripts/reporting/build_phase27_ir_source_inventory.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/jobs/build_semantic_ir_evidence.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --mock --json
python 08_scripts/reporting/build_phase27_industry_forecast_evidence.py --theme ai_optical_interconnect --mock --json
python 08_scripts/verification/validate_phase27_semantic_variable_pack_integration.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --mock --json
python 08_scripts/verification/validate_phase27_semantic_evidence_gate_impact.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --mock --json
python 08_scripts/reporting/build_phase27_semantic_evidence_summary.py --mock --json
```

## Phase 28: Real IR Source Connector + Semantic Evidence Persistence v1

Phase 28 connects the Phase 27 semantic extraction pipeline to real local source
metadata and persists gated semantic extractions as evidence graph candidates.
The first version remains conservative: it consumes already available parsed
filing/source/news metadata, does not fetch or write raw HTML/PDF, keeps mock
fallback explicit, and only writes normalized metadata or candidate rows in
execute mode.

Current Phase 27 checkpoint:

- Commit: `070874104f02af29b4fdad066eed85973b7a7981`
- Stage: `Phase 27: Semantic IR & Industry Forecast Evidence Extractor v1`
- Semantic extraction schema, chunker, retriever, mock extractor, rule gate, and
  variable pack integration are working.
- Mock semantic summary produced sources, candidate chunks, semantic
  extractions, gate results, and variable pack updates without creating pending
  review.
- The next step is to use real source URLs and persist quoted-span evidence
  candidates.

### Phase 28 Goals

1. Add real IR source connector for normalized source metadata.
2. Integrate real sources into IR source inventory.
3. Add real source document loader for parsed text or normalized snippets.
4. Run semantic extraction on real-source chunks with mock extractor by default.
5. Convert passed gate results into semantic evidence candidates.
6. Support dry-run and execute persistence modes.
7. Validate persisted candidate impact on variable packs.
8. Validate expectation gap, valuation, and bear case impact.
9. Add real IR semantic summary dashboard.
10. Update connector registry conservatively.

### Phase 28 Guardrails

- Dry-run does not write DB rows.
- Execute writes only normalized source metadata or evidence candidates.
- Raw HTML, raw PDFs, and large logs are not written by Phase 28 scripts.
- Mock evidence is explicitly marked and is not written as real evidence.
- Source URL is required for persistence.
- Quoted span is required for persistence.
- Source id, chunk id, and quoted span are used for dedupe.
- Semantic evidence is never usable for promotion by itself.
- Supplier share, ASP, shipment, customer allocation, and official consensus are
  not fabricated.
- Promotion rules remain unchanged.
- No paper orders, paper positions, or real trades are created.

### Phase 28 New Artifacts

- `08_scripts/lib/smr_real_ir_source_connector.py`
- `08_scripts/lib/smr_real_ir_document_loader.py`
- `08_scripts/lib/smr_semantic_evidence_persistence.py`
- `08_scripts/jobs/fetch_real_ir_sources.py`
- `08_scripts/jobs/persist_semantic_evidence_candidates.py`
- `08_scripts/reporting/build_phase28_real_ir_source_summary.py`
- `08_scripts/reporting/build_phase28_ir_source_inventory.py`
- `08_scripts/reporting/build_phase28_real_ir_semantic_summary.py`
- `08_scripts/verification/validate_phase28_persisted_semantic_variable_pack.py`
- `08_scripts/verification/validate_phase28_persisted_semantic_gate_impact.py`
- `docs/plans/2026-05-23-phase28-real-ir-semantic-evidence-persistence.md`

### Phase 28 Expected Behavior

- Real IR source connector can dry-run against local source metadata.
- Real source inventory prefers real sources and reports mock fallback clearly.
- Document loader returns chunks or explicit `text_unavailable`.
- Semantic extraction keeps `source_url`, `source_id`, `chunk_id`, and
  `quoted_span`.
- Persistence dry-run creates candidates in memory only.
- Persistence execute writes deduped candidate rows and no raw source text.
- Persisted candidates can update partial/context variable evidence but cannot
  add confirmed supplier share, confirmed ASP, confirmed customer allocation, or
  official consensus.
- Gate impact validators report before/after without creating pending review.

### Phase 28 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase27_semantic_evidence_summary.py --mock --json
python 08_scripts/jobs/fetch_real_ir_sources.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --dry-run --json
python 08_scripts/reporting/build_phase28_ir_source_inventory.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/jobs/build_semantic_ir_evidence.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --real-sources --mock --json
python 08_scripts/jobs/persist_semantic_evidence_candidates.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --dry-run --json
python 08_scripts/verification/validate_phase28_persisted_semantic_variable_pack.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/verification/validate_phase28_persisted_semantic_gate_impact.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase28_real_ir_semantic_summary.py --json
python 08_scripts/reporting/build_phase23_connector_availability_dashboard.py --json
```

## Phase 30: Semantic Evidence Quality & Persistence Hardening v1

Phase 30 hardens Phase 29 semantic evidence candidates before they enter the
evidence graph. The phase does not expand the watchlist or broaden extraction
scope. It scores candidate quality, filters noisy table/PPT/metadata fragments,
adds execute-time persistence guards, and audits the impact of persisted
semantic candidates.

Current Phase 29 checkpoint:

- Commit: `1fd7ac1b629abf2e964b920bf173034a87a11013`
- Stage: `Phase 29: Real IR Document Text Extraction v1`
- `text_extracted=12`
- `semantic_extractions=88`
- `evidence_candidates_created=66`
- `evidence_candidates_written=0`
- Next step is candidate quality scoring, noise filtering, and safe
  persistence.

### Phase 30 Goals

1. Add semantic evidence quality scoring.
2. Add semantic evidence noise filter.
3. Add persistence execute guard.
4. Add candidate review summary.
5. Add post-persistence audit.
6. Add download unavailable repair plan.
7. Harden table/PPT quality gates.
8. Add semantic evidence hardening summary.
9. Update connector registry conservatively.

### Phase 30 Guardrails

- Dry-run does not write DB rows.
- Execute writes only quality-scored, non-noisy, deduped candidates.
- Review-required candidates are not written by default.
- Table fragments, PPT title-only spans, headers, footers, disclaimers, and
  metadata-only snippets are rejected.
- Clean text cache and raw PDF/HTML files are not committed.
- OCR is not enabled by default.
- `usable_for_promotion` remains false.
- Semantic evidence cannot create pending review by itself.
- Supplier share, ASP, customer allocation, official consensus, customer names,
  and shipment values are not fabricated.
- Promotion rules remain unchanged.
- No paper orders, paper positions, or real trades are created.

### Phase 30 New Artifacts

- `08_scripts/lib/smr_semantic_evidence_quality.py`
- `08_scripts/lib/smr_semantic_evidence_noise_filter.py`
- `08_scripts/reporting/build_phase30_semantic_evidence_quality_report.py`
- `08_scripts/reporting/build_phase30_candidate_review_summary.py`
- `08_scripts/reporting/build_phase30_download_unavailable_repair_plan.py`
- `08_scripts/reporting/build_phase30_semantic_evidence_hardening_summary.py`
- `08_scripts/verification/validate_phase30_post_persistence_audit.py`
- `docs/plans/2026-05-23-phase30-semantic-evidence-quality-persistence-hardening.md`

### Phase 30 Expected Behavior

- Every semantic evidence candidate receives a 0-100 quality score and bucket.
- Missing `quoted_span`, missing `source_url`, and `unknown` variable type are
  rejected.
- Management commentary can be usable, but is capped below high quality.
- Direct quantified disclosures score higher than context-only fragments.
- Noisy table/PPT/metadata fragments are rejected before persistence.
- Execute mode uses quality, noise, dedupe, and promotion-safety guards.
- Post-persistence audit reports impact without creating confirmed variables or
  pending review.

### Phase 30 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase29_text_extraction_summary.py --json
python 08_scripts/reporting/build_phase30_semantic_evidence_quality_report.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase30_candidate_review_summary.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/jobs/persist_semantic_evidence_candidates.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --use-text-cache --dry-run --quality-report --json
python 08_scripts/jobs/persist_semantic_evidence_candidates.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --use-text-cache --execute --min-quality-score 50 --reject-noisy --json
python 08_scripts/verification/validate_phase30_post_persistence_audit.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase30_download_unavailable_repair_plan.py --json
python 08_scripts/reporting/build_phase30_semantic_evidence_hardening_summary.py --json
python 08_scripts/reporting/build_phase23_connector_availability_dashboard.py --json
```

## Phase 29: Real IR Document Text Extraction v1

Phase 29 upgrades real IR source metadata into clean, auditable text that can be
chunked, semantically extracted, gated, and persisted as quoted-span evidence
candidates. The phase focuses on text extraction quality rather than promotion:
metadata-only source records are not treated as body text, OCR is not enabled by
default, and raw PDF/HTML files are not committed.

Current Phase 28 checkpoint:

- Commit: `e7460440f6d54295cfd12148d4619bc57a8ccb69`
- Stage: `Phase 28: Real IR Source Connector + Semantic Evidence Persistence v1`
- Real IR source metadata is connected.
- Real source semantic pipeline can run, but many sources remain
  `text_unavailable`.
- Phase 28 summary had `text_unavailable_sources=11` and
  `evidence_candidates_created=0`.
- Bottleneck is CNINFO / IR PDF and announcement body extraction.

### Phase 29 Goals

1. Add document text extraction schema and quality statuses.
2. Add PDF / HTML / plain text / local text extractor.
3. Add ignored clean text cache.
4. Add IR section splitter.
5. Connect extracted text to the real source loader and chunker.
6. Re-run semantic extraction on extracted text.
7. Create semantic evidence candidates from extracted text.
8. Revalidate variable packs, expectation gap, valuation, and bear case impact.
9. Add text extraction summary dashboard.
10. Update connector registry conservatively.

### Phase 29 Guardrails

- Dry-run does not write cache or DB rows.
- Execute writes only clean text cache and evidence candidates.
- Raw PDF and raw HTML are not written by Phase 29 scripts.
- Generated text cache is ignored by git.
- Metadata-only text cannot enter semantic chunking.
- Text that is too short, table-only, or scanned-PDF-without-text is skipped.
- OCR is not enabled by default.
- Quoted span must come from extracted chunk text.
- Source URL is required before evidence candidate persistence.
- Semantic evidence remains promotion-disabled by default.
- Supplier share, ASP, shipment, customer allocation, and customer names are not
  fabricated.
- Semantic evidence alone cannot create pending review.
- Promotion rules remain unchanged.
- No paper orders, paper positions, or real trades are created.

### Phase 29 New Artifacts

- `08_scripts/lib/smr_document_text_extraction.py`
- `08_scripts/lib/smr_document_text_extractor.py`
- `08_scripts/lib/smr_text_cache.py`
- `08_scripts/lib/smr_ir_section_splitter.py`
- `08_scripts/jobs/extract_real_ir_document_text.py`
- `08_scripts/reporting/build_phase29_text_extraction_summary.py`
- `08_scripts/verification/validate_phase29_text_extraction_semantic_evidence.py`
- `docs/plans/2026-05-23-phase29-real-ir-document-text-extraction.md`

### Phase 29 Expected Behavior

- Document extraction reports `text_extracted`, `text_too_short`,
  `metadata_only`, `scanned_pdf_needs_ocr`, `table_only`, or
  `extraction_failed`.
- Text cache can be written in execute mode and read by the semantic pipeline.
- Section splitter preserves Q&A and classifies useful IR sections.
- Chunker preserves source URL, published date, section type, text source, and
  extraction status.
- Semantic extraction can run from text cache while defaulting to mock mode.
- Persistence dry-run can create candidates only when extracted text has valid
  quoted spans and source URLs.
- Revalidation reports impact without creating pending review.

### Phase 29 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase28_real_ir_semantic_summary.py --json
python 08_scripts/jobs/extract_real_ir_document_text.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --dry-run --json
python 08_scripts/jobs/build_semantic_ir_evidence.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --real-sources --use-text-cache --mock --json
python 08_scripts/jobs/persist_semantic_evidence_candidates.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --use-text-cache --dry-run --json
python 08_scripts/verification/validate_phase29_text_extraction_semantic_evidence.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase29_text_extraction_summary.py --json
python 08_scripts/reporting/build_phase23_connector_availability_dashboard.py --json
```
