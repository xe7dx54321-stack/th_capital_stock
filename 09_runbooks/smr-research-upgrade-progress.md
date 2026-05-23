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
