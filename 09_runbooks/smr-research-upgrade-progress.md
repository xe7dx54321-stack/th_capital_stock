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

## Phase 46: Paper Watchlist Tracking v1

Phase 46 moves `300308.SZ` from a bounded final research conclusion into
research-only paper watchlist tracking. The watchlist records a lifecycle entry,
tracking variables, trigger conditions, audit records, thesis strength score,
status updates, review packet, and dashboard. It does not create pending human
review, approved paper, paper order, paper position, target price, position
guidance, or real trade.

Current Phase 45 checkpoint:

- Commit: `8b6ec93bd3cad0e0a05225a791b459c760dcf01a`
- Stage: `Phase 45: Final Research Packet Review v1`
- `300308.SZ`: final thesis = `research_supported_but_not_investment_ready`
- Research evidence = `sufficient_for_watchlist_research`
- Investment pending evidence = `insufficient`
- Final conclusion = `formal_research_conclusion_positive_watchlist`
- Paper watchlist readiness = `paper_watchlist_candidate`
- `pending_human_review_allowed=false`
- `paper_order_allowed=false`
- `promotion_allowed_true=0`
- `real_trade_created=0`
- `300394.SZ`: remains `repair_required_before_review`

### Phase 46 Goals

1. Create paper watchlist entry.
2. Add paper watchlist lifecycle validation.
3. Define tracking variables.
4. Define tracking trigger conditions.
5. Add watchlist entry upsert.
6. Add watchlist audit report.
7. Add thesis strength tracking score.
8. Add watchlist status update and validator.
9. Add paper watchlist review packet.
10. Add paper watchlist dashboard.

### Phase 46 Guardrails

- Watchlist entry does not mean `pending_human_review`.
- Watchlist entry does not mean approved paper, paper order, or paper position.
- Tracking trigger does not mean trading signal.
- Thesis strengthening does not mean investment action.
- Supplier share remains scenario-only.
- Official consensus remains unconfirmed.
- Customer allocation remains proxy-only.
- `pending_created=0`.
- `paper_order_created=0`.
- `real_trade_created=0`.
- Promotion rules remain unchanged.
- No raw PDF, raw HTML, cache, DB, log, or generated artifacts are committed.

### Phase 46 New Artifacts

- `08_scripts/lib/smr_paper_watchlist_entry.py`
- `08_scripts/lib/smr_paper_watchlist_lifecycle.py`
- `08_scripts/lib/smr_paper_watchlist_tracking_variables.py`
- `08_scripts/lib/smr_paper_watchlist_triggers.py`
- `08_scripts/lib/smr_paper_watchlist_audit.py`
- `08_scripts/lib/smr_thesis_strength_tracking.py`
- `08_scripts/jobs/upsert_phase46_paper_watchlist_entry.py`
- `08_scripts/jobs/update_phase46_watchlist_status.py`
- `08_scripts/verification/validate_phase46_watchlist_status_update.py`
- `08_scripts/reporting/build_phase46_paper_watchlist_entry.py`
- `08_scripts/reporting/build_phase46_tracking_variables.py`
- `08_scripts/reporting/build_phase46_tracking_triggers.py`
- `08_scripts/reporting/build_phase46_watchlist_audit_report.py`
- `08_scripts/reporting/build_phase46_thesis_strength_score.py`
- `08_scripts/reporting/build_phase46_paper_watchlist_review_packet.py`
- `08_scripts/reporting/build_phase46_paper_watchlist_dashboard.py`
- `docs/plans/2026-05-24-phase46-paper-watchlist-tracking.md`

### Phase 46 Expected Behavior

For `300308.SZ`, Phase 46 creates an idempotent research-only watchlist entry.
The first execute moves the entry to `active_tracking`; later status updates can
mark it `tracking_strengthened`, `tracking_weakened`, or
`tracking_needs_more_evidence` without creating pending, paper orders,
positions, or real trades. Dashboard active tracking counts include the active
tracking family so a strengthened watchlist item still remains in the tracking
pool.

### Phase 46 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase45_final_review_dashboard.py --json
python 08_scripts/reporting/build_phase46_paper_watchlist_entry.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase46_tracking_variables.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase46_tracking_triggers.py --ticker 300308.SZ --json
python 08_scripts/jobs/upsert_phase46_paper_watchlist_entry.py --ticker 300308.SZ --dry-run --json
python 08_scripts/jobs/upsert_phase46_paper_watchlist_entry.py --ticker 300308.SZ --execute --json
python 08_scripts/reporting/build_phase46_watchlist_audit_report.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase46_thesis_strength_score.py --ticker 300308.SZ --json
python 08_scripts/jobs/update_phase46_watchlist_status.py --ticker 300308.SZ --status tracking_strengthened --dry-run --json
python 08_scripts/jobs/update_phase46_watchlist_status.py --ticker 300308.SZ --status tracking_strengthened --execute --json
python 08_scripts/verification/validate_phase46_watchlist_status_update.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase46_paper_watchlist_review_packet.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase46_paper_watchlist_dashboard.py --json
```

## Phase 45: Final Research Packet Review v1

Phase 45 returns `300308.SZ` from the manual evidence intake governance branch
to the research mainline. It aggregates the current research assets, reviews
thesis validity, evidence sufficiency, variable coverage, expectation-gap and
valuation boundaries, bear case pressure, final research conclusion, and paper
watchlist tracking readiness. It does not create pending human review, approved
paper, paper order, position, target price, or real trade.

Current Phase 44 checkpoint:

- Commit: `b53788bf193adb3a3dc25a82439b6e0b87dbc553`
- Stage: `Phase 44: Manual Candidate Review Closeout v1`
- `300308.SZ`: manual candidates reviewed = 3
- `official_consensus`: accepted as candidate, not confirmed
- `supplier_share`: scenario-only, not confirmed
- `customer_allocation`: proxy-only, not confirmed
- `confirmed_variables_added=0`
- `pending_created=0`, `paper_order_created=0`, `promotion_allowed_true=0`
- Manual intake branch status: `closed`
- Next mainline step: `phase45_final_research_packet_review`
- `300394.SZ`: remains `repair_required_before_review`

### Phase 45 Goals

1. Build final research asset summary.
2. Build final thesis validity review.
3. Build final evidence sufficiency review.
4. Build final variable coverage review.
5. Build expectation-gap and valuation-boundary review.
6. Build final bear case review.
7. Build final research conclusion classifier.
8. Build paper watchlist readiness packet.
9. Build final research packet.
10. Build final review dashboard.

### Phase 45 Guardrails

- Formal research conclusion does not mean trading recommendation.
- `paper_watchlist_candidate` does not mean `pending_human_review`.
- Official consensus candidate remains unconfirmed.
- Supplier share remains scenario-only.
- Customer allocation remains proxy-only.
- Research sufficiency and investment pending sufficiency are separate.
- `pending_created=0`.
- `paper_order_created=0`.
- `real_trade_created=0`.
- `promotion_allowed_true=0`.
- No target price or position guidance is generated.
- No raw PDF, raw HTML, cache, DB, log, or generated artifacts are committed.

### Phase 45 New Artifacts

- `08_scripts/lib/smr_final_research_asset_aggregator.py`
- `08_scripts/lib/smr_final_thesis_review.py`
- `08_scripts/lib/smr_final_research_conclusion.py`
- `08_scripts/reporting/build_phase45_final_research_asset_summary.py`
- `08_scripts/reporting/build_phase45_final_thesis_review.py`
- `08_scripts/reporting/build_phase45_final_evidence_sufficiency_review.py`
- `08_scripts/reporting/build_phase45_final_variable_coverage_review.py`
- `08_scripts/reporting/build_phase45_expectation_gap_valuation_boundary.py`
- `08_scripts/reporting/build_phase45_final_bear_case_review.py`
- `08_scripts/reporting/build_phase45_final_research_conclusion.py`
- `08_scripts/reporting/build_phase45_paper_watchlist_readiness_packet.py`
- `08_scripts/reporting/build_phase45_final_research_packet.py`
- `08_scripts/reporting/build_phase45_final_review_dashboard.py`
- `docs/plans/2026-05-24-phase45-final-research-packet-review.md`

### Phase 45 Expected Behavior

For `300308.SZ`, Phase 45 may classify the research package as
`formal_research_conclusion_positive_watchlist` with
`paper_watchlist_candidate` readiness, but only for tracking. It keeps
investment pending blocked because supplier share, official consensus, customer
allocation, and valuation support remain unconfirmed or scenario-bound. The
next phase should be `phase46_paper_watchlist_tracking`.

### Phase 45 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase44_closeout_dashboard.py --json
python 08_scripts/reporting/build_phase45_final_research_asset_summary.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase45_final_thesis_review.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase45_final_evidence_sufficiency_review.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase45_final_variable_coverage_review.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase45_expectation_gap_valuation_boundary.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase45_final_bear_case_review.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase45_final_research_conclusion.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase45_paper_watchlist_readiness_packet.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase45_final_research_packet.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase45_final_research_packet.py --ticker 300308.SZ --markdown
python 08_scripts/reporting/build_phase45_final_review_dashboard.py --json
```

## Phase 44: Manual Candidate Review Closeout v1

Phase 44 closes the manual evidence intake / candidate governance branch for
`300308.SZ`. It reviews the three Phase 43 manual candidates with controlled
actions, writes lifecycle and audit records, finalizes allowed usage, and
revalidates research packet impact without confirming variables or relaxing
promotion. After this phase, the next step returns to the main research packet
review line rather than adding more evidence-governance phases.

Current Phase 43 checkpoint:

- Commit: `c204908ff68c189a7306b2ac6505a0f3407f4c69`
- Stage: `Phase 43: Manual Source Intake Candidate Generation v1`
- `300308.SZ`: manual candidates written = 3
- `official_consensus_candidate`: candidate added, not confirmed
- `supplier_share_scenario`: scenario-only, not confirmed
- `customer_allocation_proxy`: proxy/context only, not confirmed
- `confirmed_variables_added=0`
- `pending_created=0`, `paper_order_created=0`, `promotion_allowed_true=0`
- `300394.SZ`: remains `repair_required_before_review`

### Phase 44 Goals

1. Add manual candidate review lifecycle states.
2. Add controlled manual candidate review actions.
3. Write manual candidate review audit records.
4. Finalize allowed usage for official consensus, supplier-share scenario, and
   customer-allocation proxy candidates.
5. Validate research packet impact as better bounded but not upgraded.
6. Build the manual candidate closeout packet.
7. Build the mainline transition plan pointing to Phase 45.
8. Build closeout dashboard and optional read-only HTML.

### Phase 44 Guardrails

- `accept_as_candidate` does not confirm evidence.
- Official consensus candidate remains `candidate_not_confirmed`.
- Supplier share is closed as `scenario_analysis_only`, not fact.
- Customer allocation is closed as proxy/context only, not confirmed
  allocation.
- Review actions are not connected to the promotion gate.
- Forbidden actions such as `allow_promotion`, `create_pending`, paper order,
  position, or trade creation are intercepted.
- `confirmed_variables_added=0`.
- `usable_for_promotion_true=0`.
- `pending_created=0`.
- `paper_order_created=0`.
- No approved paper, paper position, broker adapter, or real trading path is
  created.
- Raw PDF, raw HTML, cache, DB, log, and generated HTML artifacts are not
  committed.

### Phase 44 New Artifacts

- `08_scripts/lib/smr_manual_candidate_review_lifecycle.py`
- `08_scripts/lib/smr_manual_candidate_review_actions.py`
- `08_scripts/lib/smr_manual_candidate_review_audit.py`
- `08_scripts/jobs/apply_phase44_manual_candidate_review_action.py`
- `08_scripts/reporting/build_phase44_manual_candidate_review_audit.py`
- `08_scripts/reporting/build_phase44_manual_candidate_final_usage_matrix.py`
- `08_scripts/verification/validate_phase44_manual_candidate_research_impact_closeout.py`
- `08_scripts/reporting/build_phase44_manual_candidate_closeout_packet.py`
- `08_scripts/reporting/build_phase44_mainline_transition_plan.py`
- `08_scripts/reporting/build_phase44_closeout_dashboard.py`
- `08_scripts/reporting/build_phase44_closeout_html.py`
- `docs/plans/2026-05-24-phase44-manual-candidate-review-closeout.md`

### Phase 44 Expected Behavior

For `300308.SZ`, the official consensus candidate is accepted as a candidate
only, supplier share is marked scenario-only, and customer allocation is marked
proxy-only. All three actions write audit records and lifecycle states. The
manual intake branch status becomes `closed`, and the next mainline step is
`phase45_final_research_packet_review`.

### Phase 44 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase43_manual_intake_dashboard.py --json
python 08_scripts/jobs/apply_phase44_manual_candidate_review_action.py --ticker 300308.SZ --candidate-type official_consensus --action accept_as_candidate --dry-run --json
python 08_scripts/jobs/apply_phase44_manual_candidate_review_action.py --ticker 300308.SZ --candidate-type supplier_share --action mark_as_scenario_only --dry-run --json
python 08_scripts/jobs/apply_phase44_manual_candidate_review_action.py --ticker 300308.SZ --candidate-type customer_allocation --action mark_as_proxy_only --dry-run --json
python 08_scripts/jobs/apply_phase44_manual_candidate_review_action.py --ticker 300308.SZ --candidate-type official_consensus --action accept_as_candidate --execute --json
python 08_scripts/jobs/apply_phase44_manual_candidate_review_action.py --ticker 300308.SZ --candidate-type supplier_share --action mark_as_scenario_only --execute --json
python 08_scripts/jobs/apply_phase44_manual_candidate_review_action.py --ticker 300308.SZ --candidate-type customer_allocation --action mark_as_proxy_only --execute --json
python 08_scripts/reporting/build_phase44_manual_candidate_review_audit.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase44_manual_candidate_final_usage_matrix.py --ticker 300308.SZ --json
python 08_scripts/verification/validate_phase44_manual_candidate_research_impact_closeout.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase44_manual_candidate_closeout_packet.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase44_mainline_transition_plan.py --json
python 08_scripts/reporting/build_phase44_closeout_dashboard.py --json
python 08_scripts/reporting/build_phase44_closeout_html.py --output 09_runbooks/generated/phase44_closeout.html
```

## Phase 43: Manual Source Intake Candidate Generation v1

Phase 43 turns the Phase 42 manual/authorized-source intake framework into a
bounded candidate-generation mechanism. It uses deterministic sample payloads
for `300308.SZ` to show which manual inputs can become candidates, which inputs
must be rejected, and how permission and allowed-usage guards prevent manual
source intake from contaminating confirmed research variables.

Current Phase 42 checkpoint:

- Commit: `b157d700433da8aa8261b814f3aea045ce14df5e`
- Stage: `Phase 42: Follow-up Evidence Fulfillment & Manual Source Intake v1`
- `300308.SZ`: three follow-up requests remain open/bounded.
- `official_consensus`: authorized source required; not confirmed.
- `supplier_share`: scenario-only; not confirmed.
- `confirmed_customer_allocation`: proxy-only; not confirmed.
- `pending_created=0`, `paper_order_created=0`, `promotion_allowed_true=0`
- `300394.SZ`: remains `repair_required_before_review`

### Phase 43 Goals

1. Define manual source intake payload samples for official consensus, supplier
   share scenario, and customer allocation proxy.
2. Generate manual evidence candidates from valid sample payloads.
3. Generate rejection records for invalid manual inputs, including internal
   proxy attempts to impersonate official consensus.
4. Apply permission and allowed-usage guards, including scenario/proxy
   downgrades.
5. Build a manual intake review queue with explicit forbidden actions.
6. Support guarded persistence of manual candidates while keeping all
   candidates non-confirmed and promotion-disabled.
7. Revalidate research packet impact as better bounded but not upgraded to
   confirmed evidence.
8. Produce dashboard and read-only static HTML outputs.

### Phase 43 Guardrails

- Candidate is not confirmed evidence.
- Supplier share scenario is not supplier share fact.
- Customer allocation proxy is not confirmed customer allocation.
- Authorized consensus candidate is not pending review.
- Internal proxy cannot satisfy official consensus.
- Unauthorized or incomplete payloads are rejected with recommended fixes.
- `usable_for_promotion=false` for every manual candidate.
- `pending_created=0`.
- `paper_order_created=0`.
- `promotion_allowed_true=0`.
- No approved paper, paper position, broker adapter, or real trading path is
  created.
- Raw PDF, raw HTML, text cache, DB, log, and generated HTML artifacts are not
  committed.

### Phase 43 New Artifacts

- `08_scripts/lib/smr_manual_intake_payload.py`
- `08_scripts/lib/smr_manual_intake_candidate_generator.py`
- `08_scripts/lib/smr_manual_intake_permission_guard.py`
- `08_scripts/lib/smr_manual_intake_rejection.py`
- `08_scripts/jobs/build_phase43_manual_intake_candidates.py`
- `08_scripts/jobs/persist_phase43_manual_intake_candidates.py`
- `08_scripts/reporting/build_phase43_manual_intake_samples.py`
- `08_scripts/reporting/build_phase43_manual_intake_permission_audit.py`
- `08_scripts/reporting/build_phase43_manual_intake_review_queue.py`
- `08_scripts/reporting/build_phase43_manual_intake_rejection_report.py`
- `08_scripts/reporting/build_phase43_manual_intake_dashboard.py`
- `08_scripts/reporting/build_phase43_manual_intake_html.py`
- `08_scripts/verification/validate_phase43_manual_intake_research_impact.py`
- `docs/plans/2026-05-24-phase43-manual-source-intake-candidate-generation.md`

### Phase 43 Expected Behavior

For `300308.SZ`, the system should create one official-consensus candidate, one
supplier-share scenario candidate, and one customer-allocation proxy candidate.
The official consensus candidate remains unconfirmed, the supplier-share
scenario remains scenario-only, and the customer-allocation proxy remains
proxy-only. A bad internal consensus proxy sample is rejected with a recommended
fix. The research packet gains better boundaries but no confirmed variables, no
pending review, no paper order, and no promotion relaxation.

### Phase 43 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase42_fulfillment_dashboard.py --json
python 08_scripts/reporting/build_phase43_manual_intake_samples.py --ticker 300308.SZ --json
python 08_scripts/jobs/build_phase43_manual_intake_candidates.py --ticker 300308.SZ --dry-run --json
python 08_scripts/jobs/build_phase43_manual_intake_candidates.py --ticker 300308.SZ --execute --json
python 08_scripts/reporting/build_phase43_manual_intake_permission_audit.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase43_manual_intake_review_queue.py --ticker 300308.SZ --json
python 08_scripts/jobs/persist_phase43_manual_intake_candidates.py --ticker 300308.SZ --dry-run --json
python 08_scripts/jobs/persist_phase43_manual_intake_candidates.py --ticker 300308.SZ --execute --json
python 08_scripts/reporting/build_phase43_manual_intake_rejection_report.py --ticker 300308.SZ --json
python 08_scripts/verification/validate_phase43_manual_intake_research_impact.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase43_manual_intake_dashboard.py --json
python 08_scripts/reporting/build_phase43_manual_intake_html.py --output 09_runbooks/generated/phase43_manual_intake.html
```

## Phase 42: Follow-up Evidence Fulfillment & Manual Source Intake v1

Phase 42 starts consuming the three Phase 41 follow-up requests for
`300308.SZ`. It adds a safe fulfillment frame for authorized/manual source
metadata, supplier-share scenario assumptions, and customer-allocation
proxy-vs-confirmed audit. The stage does not ingest raw files or write evidence;
it defines which inputs could become candidates later, which remain scenario or
proxy only, and why pending remains blocked.

Current Phase 41 checkpoint:

- Commit: `9e776702b7dee8771d8efa0082c81a5ae0c7aafd`
- Stage: `Phase 41: Research Review Follow-up Task Execution v1`
- `300308.SZ`: `followup_queue_items=3`, `audit_records=3`
- `official_consensus`: `commercial_source_required`
- `supplier_share`: `not_publicly_confirmable`, scenario-only
- `confirmed_customer_allocation`: `proxy_only`
- `pending_created=0`, `paper_order_created=0`, `promotion_allowed_true=0`
- `300394.SZ`: remains `repair_required_before_review`

### Phase 42 Goals

1. Build follow-up request fulfillment state for the three core requests.
2. Generate manual source intake templates without writing source rows.
3. Validate manual source intake samples and reject internal proxies for
   official consensus.
4. Build official consensus fulfillment requirements for authorized/manual
   metadata.
5. Build supplier-share scenario registry with confirmed status disabled.
6. Audit customer-allocation proxy evidence against confirmed-allocation misuse.
7. Build the follow-up fulfillment packet and dashboard.
8. Revalidate research packet impact as unchanged but better bounded.
9. Generate optional read-only static HTML under ignored output paths.

### Phase 42 Guardrails

- Open requests are not evidence.
- Manual source input is not automatically confirmed evidence.
- Official consensus requires authorized or user-provided source metadata.
- Internal proxy cannot fulfill official consensus.
- Supplier share scenario assumptions remain `scenario_analysis_only`.
- Customer-allocation proxy remains proxy-only until direct disclosure appears.
- Scenario assumptions do not enter the promotion gate.
- `pending_created=0`.
- `paper_order_created=0`.
- `promotion_allowed_true=0`.
- No approved paper, paper position, broker adapter, or real trading path is
  created.
- Raw PDF, raw HTML, text cache, DB, log, and generated HTML artifacts are not
  committed.

### Phase 42 New Artifacts

- `08_scripts/lib/smr_followup_fulfillment_state.py`
- `08_scripts/lib/smr_manual_source_intake.py`
- `08_scripts/lib/smr_manual_source_intake_validator.py`
- `08_scripts/lib/smr_official_consensus_fulfillment.py`
- `08_scripts/lib/smr_supplier_share_scenario_registry.py`
- `08_scripts/lib/smr_customer_allocation_proxy_audit.py`
- `08_scripts/jobs/validate_phase42_manual_source_intake.py`
- `08_scripts/reporting/build_phase42_followup_fulfillment_state.py`
- `08_scripts/reporting/build_phase42_manual_source_intake_template.py`
- `08_scripts/reporting/build_phase42_official_consensus_fulfillment.py`
- `08_scripts/reporting/build_phase42_supplier_share_scenario_registry.py`
- `08_scripts/reporting/build_phase42_customer_allocation_proxy_audit.py`
- `08_scripts/reporting/build_phase42_followup_fulfillment_packet.py`
- `08_scripts/verification/validate_phase42_research_packet_impact.py`
- `08_scripts/reporting/build_phase42_fulfillment_dashboard.py`
- `08_scripts/reporting/build_phase42_fulfillment_html.py`
- `docs/plans/2026-05-24-phase42-followup-evidence-fulfillment-manual-source-intake.md`

### Phase 42 Expected Behavior

For `300308.SZ`, the system should show that official consensus needs
authorized source metadata, supplier share can only be used as explicit scenario
assumption unless directly disclosed, and customer allocation remains proxy-only.
The research packet impact should be `unchanged_but_better_bounded`, with
stronger why-not-pending boundaries but no confirmed variable upgrade. For
`300394.SZ`, the system remains repair-only.

### Phase 42 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase41_followup_dashboard.py --json
python 08_scripts/reporting/build_phase42_followup_fulfillment_state.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase42_manual_source_intake_template.py --ticker 300308.SZ --evidence-type official_consensus --json
python 08_scripts/jobs/validate_phase42_manual_source_intake.py --sample official_consensus --json
python 08_scripts/jobs/validate_phase42_manual_source_intake.py --sample supplier_share_scenario --json
python 08_scripts/jobs/validate_phase42_manual_source_intake.py --sample customer_allocation_proxy --json
python 08_scripts/reporting/build_phase42_official_consensus_fulfillment.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase42_supplier_share_scenario_registry.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase42_customer_allocation_proxy_audit.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase42_followup_fulfillment_packet.py --ticker 300308.SZ --json
python 08_scripts/verification/validate_phase42_research_packet_impact.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase42_fulfillment_dashboard.py --json
python 08_scripts/reporting/build_phase42_fulfillment_html.py --output 09_runbooks/generated/phase42_fulfillment.html
```

## Phase 41: Research Review Follow-up Task Execution v1

Phase 41 converts the Phase 40 research action `request_deeper_research` into
specific, auditable follow-up evidence tasks. The stage focuses on three
remaining `300308.SZ` gaps: official consensus, supplier share, and confirmed
customer allocation. These are task requests and source-route checks only; they
do not write evidence or create investment pending.

Current Phase 40 checkpoint:

- Commit: `15d25b6d0c047cc4644567391114032b53d64ca4`
- Stage: `Phase 40: Research Review Workbench v1`
- `300308.SZ`: lifecycle moved from `research_review_candidate` to
  `reviewed_request_deeper_research`
- `audit_records=1`, `pending_created=0`, `paper_order_created=0`
- `300394.SZ`: `repair_required_before_review`, excluded from research
  follow-up tasks

### Phase 41 Goals

1. Detect Phase 40 follow-up triggers from lifecycle and audit state.
2. Execute controlled specific evidence requests for `official_consensus`,
   `supplier_share`, and `confirmed_customer_allocation`.
3. Report official consensus source availability without impersonating
   authorized consensus.
4. Report supplier share public availability caveats and scenario-only usage.
5. Report customer allocation proxy boundaries and direct-confirmation routes.
6. Build the research follow-up queue and follow-up audit report.
7. Validate the system remains research-only after follow-up task creation.
8. Produce the follow-up dashboard and optional read-only static HTML.

### Phase 41 Guardrails

- Specific evidence requests are not evidence.
- Official consensus request is not confirmed official consensus.
- Internal proxy remains supporting context only.
- Supplier share remains scenario analysis unless directly disclosed.
- Customer allocation proxy is not confirmed allocation.
- North America customer references are not converted into NVIDIA allocation.
- `promotion_allowed=false`.
- `pending_created=0`.
- `paper_order_created=0`.
- No approved paper, paper position, broker adapter, or real trading path is
  created.
- Raw PDF, raw HTML, text cache, DB, log, and generated HTML artifacts are not
  committed.

### Phase 41 New Artifacts

- `08_scripts/lib/smr_research_followup_trigger.py`
- `08_scripts/lib/smr_research_followup_queue.py`
- `08_scripts/lib/smr_research_followup_audit.py`
- `08_scripts/lib/smr_official_consensus_availability.py`
- `08_scripts/lib/smr_supplier_share_route.py`
- `08_scripts/lib/smr_customer_allocation_route.py`
- `08_scripts/jobs/execute_phase41_specific_evidence_requests.py`
- `08_scripts/reporting/build_phase41_followup_trigger_summary.py`
- `08_scripts/reporting/build_phase41_official_consensus_availability.py`
- `08_scripts/reporting/build_phase41_supplier_share_route.py`
- `08_scripts/reporting/build_phase41_customer_allocation_route.py`
- `08_scripts/reporting/build_phase41_research_followup_queue.py`
- `08_scripts/reporting/build_phase41_followup_audit_report.py`
- `08_scripts/verification/validate_phase41_research_only_revalidation.py`
- `08_scripts/reporting/build_phase41_followup_dashboard.py`
- `08_scripts/reporting/build_phase41_followup_html.py`
- `docs/plans/2026-05-24-phase41-research-review-followup-task-execution.md`

### Phase 41 Expected Behavior

For `300308.SZ`, the system should show exactly which follow-up evidence tasks
were created, where each evidence type could be pursued, what each task may and
may not support, and why nothing has become pending or confirmed. For
`300394.SZ`, the system should keep the ticker in repair-only mode until the
evidence chain is restored.

### Phase 41 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase40_research_review_dashboard.py --json
python 08_scripts/reporting/build_phase41_followup_trigger_summary.py --json
python 08_scripts/jobs/execute_phase41_specific_evidence_requests.py --ticker 300308.SZ --dry-run --json
python 08_scripts/jobs/execute_phase41_specific_evidence_requests.py --ticker 300308.SZ --execute --json
python 08_scripts/reporting/build_phase41_official_consensus_availability.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase41_supplier_share_route.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase41_customer_allocation_route.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase41_research_followup_queue.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase41_followup_audit_report.py --json
python 08_scripts/verification/validate_phase41_research_only_revalidation.py --json
python 08_scripts/reporting/build_phase41_followup_dashboard.py --json
python 08_scripts/reporting/build_phase41_followup_html.py --output 09_runbooks/generated/phase41_followup.html
```

## Phase 40: Research Review Workbench v1

Phase 40 connects the Phase 39 `300308.SZ` `research_review_candidate` to a
research-only workbench. The workbench lets a human researcher inspect the
evidence-strengthened packet, checklist, why-not-pending blockers, and next
evidence priorities, then record research actions with audit history. It remains
outside investment pending and outside trading.

Current Phase 39 checkpoint:

- Commit: `342337fe14462f524aed9b43eb580c2b2da9e43b`
- Stage: `Phase 39: Evidence-Strengthened Research Packet & Review Decision v1`
- `300308.SZ`: `decision=research_review_candidate`, `confidence=medium`,
  `evidence_before=44`, `evidence_after=49`
- Strengthened variables: `product_mix`, `order_visibility`, `shipment`
- `pending_allowed=false`, `paper_order_allowed=false`
- `300394.SZ`: `repair_required_before_research_deepening`,
  `research_deepening_allowed=false`

### Phase 40 Goals

1. Add the research review lifecycle schema.
2. Build the research review queue and add `300308.SZ`.
3. Build the research review workbench packet.
4. Support research-only actions: continue evidence acquisition, deeper
   research, specific evidence request, reviewed, deprioritized, and archived.
5. Add append-only audit logging for executed actions.
6. Generate specific evidence requests without fetching or writing evidence.
7. Build the research review dashboard and post-action validator.
8. Generate optional read-only static HTML under ignored output paths.

### Phase 40 Guardrails

- `research_review_candidate` is not `pending_human_review`.
- `mark_reviewed` is not approval.
- `request_deeper_research` is not promotion.
- `request_specific_evidence` creates a request task only.
- Supplier share, customer allocation, official consensus, ASP, orders, and
  shipment values are not confirmed.
- `promotion_allowed=false`.
- `pending_created=0`.
- `paper_order_created=0`.
- No approved paper, paper position, broker adapter, or real trading path is
  created.
- Raw PDF, raw HTML, text cache, DB, log, and generated HTML artifacts are not
  committed.

### Phase 40 New Artifacts

- `08_scripts/lib/smr_research_review_lifecycle.py`
- `08_scripts/lib/smr_research_review_queue.py`
- `08_scripts/lib/smr_research_review_actions.py`
- `08_scripts/lib/smr_research_review_audit.py`
- `08_scripts/lib/smr_specific_evidence_request.py`
- `08_scripts/reporting/build_phase40_research_review_queue.py`
- `08_scripts/reporting/build_phase40_research_review_workbench_packet.py`
- `08_scripts/jobs/apply_phase40_research_review_action.py`
- `08_scripts/reporting/build_phase40_research_review_audit_report.py`
- `08_scripts/reporting/build_phase40_specific_evidence_requests.py`
- `08_scripts/reporting/build_phase40_research_review_dashboard.py`
- `08_scripts/verification/validate_phase40_research_review_post_action.py`
- `08_scripts/reporting/build_phase40_research_review_html.py`
- `docs/plans/2026-05-24-phase40-research-review-workbench.md`

### Phase 40 Expected Behavior

For `300308.SZ`, the system should show why the ticker deserves manual research
review, what the researcher should inspect, which research-only actions are
allowed, and why pending remains blocked. For `300394.SZ`, the system should
continue to show repair-required status and keep it out of the research review
queue until the evidence chain is restored.

### Phase 40 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase39_review_decision_dashboard.py --json
python 08_scripts/reporting/build_phase40_research_review_queue.py --json
python 08_scripts/reporting/build_phase40_research_review_workbench_packet.py --ticker 300308.SZ --json
python 08_scripts/jobs/apply_phase40_research_review_action.py --ticker 300308.SZ --action request_deeper_research --dry-run --json
python 08_scripts/jobs/apply_phase40_research_review_action.py --ticker 300308.SZ --action request_specific_evidence --evidence-type official_consensus --dry-run --json
python 08_scripts/jobs/apply_phase40_research_review_action.py --ticker 300308.SZ --action request_deeper_research --execute --json
python 08_scripts/reporting/build_phase40_research_review_audit_report.py --json
python 08_scripts/reporting/build_phase40_specific_evidence_requests.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase40_research_review_dashboard.py --json
python 08_scripts/verification/validate_phase40_research_review_post_action.py --json
python 08_scripts/reporting/build_phase40_research_review_html.py --output 09_runbooks/generated/phase40_research_review.html
```

## Phase 39: Evidence-Strengthened Research Packet & Review Decision v1

Phase 39 takes the five `300308.SZ` evidence candidates persisted in Phase 38
and turns them into an evidence-strengthened research packet plus a conservative
research-review decision. The key boundary is that `research_review_candidate`
means "worth a manual research review", not investment pending and not a trade
action.

Current Phase 38 checkpoint:

- Commit: `b2ad75cb5f005f33294943b73f4955f87b02f348`
- Stage: `Phase 38: Targeted Evidence Candidate Review & Persistence v1`
- `300308.SZ`: `candidates_total=15`, `eligible_for_persistence=12`,
  `candidates_written=5`, `evidence_before=44`, `evidence_after=49`,
  `quality_delta=strengthened_with_new_supporting_evidence`
- New evidence by variable: `product_mix=3`, `order_visibility=1`,
  `shipment=1`
- Still missing: `supplier_share`, `official_consensus`,
  `confirmed_customer_allocation`
- `300394.SZ`: `repair_tasks_written=5`,
  `research_deepening_allowed=false`

### Phase 39 Goals

1. Explain what each persisted evidence row supports and does not support.
2. Build the `300308.SZ` evidence-strengthened research packet.
3. Classify whether `300308.SZ` is a `research_review_candidate`.
4. Generate a human research review checklist.
5. Reinforce why the ticker is still not pending.
6. Update next evidence priority after Phase 38 improvements.
7. Show `300394.SZ` repair-only status without deepening research.
8. Produce the Phase 39 review decision dashboard.

### Phase 39 Guardrails

- `research_review_candidate` is not `pending_human_review`.
- Product mix is not upgraded into confirmed ASP.
- Order visibility is not upgraded into confirmed order.
- Shipment commentary is not a confirmed shipment number.
- Customer allocation proxy is not confirmed allocation.
- Internal proxy is not official consensus.
- `promotion_allowed=false`.
- `new_pending_created=0`.
- `paper_order_created=0`.
- Raw PDF, raw HTML, text cache, DB, log, and generated HTML artifacts are not
  committed.

### Phase 39 New Artifacts

- `08_scripts/lib/smr_evidence_contribution_analyzer.py`
- `08_scripts/lib/smr_research_review_candidate.py`
- `08_scripts/reporting/build_phase39_300308_evidence_contribution.py`
- `08_scripts/reporting/build_phase39_300308_evidence_strengthened_packet.py`
- `08_scripts/reporting/build_phase39_research_review_candidate_decision.py`
- `08_scripts/reporting/build_phase39_human_research_review_checklist.py`
- `08_scripts/reporting/build_phase39_why_not_pending_reinforcement.py`
- `08_scripts/reporting/build_phase39_next_evidence_priority_update.py`
- `08_scripts/reporting/build_phase39_300394_repair_status_summary.py`
- `08_scripts/reporting/build_phase39_review_decision_dashboard.py`
- `docs/plans/2026-05-24-phase39-evidence-strengthened-research-review-decision.md`

## Phase 38: Targeted Evidence Candidate Review & Persistence v1

Phase 38 takes the 15 `300308.SZ` dry-run evidence candidates created in Phase
37 and turns them into governed research assets. The stage reviews candidate
quality, filters noise and sensitive variables, creates a targeted review queue,
persists only a small guarded sample, refreshes the evidence chain, and then
revalidates whether the single-stock research packet became more solid.

Current Phase 37 checkpoint:

- Commit: `d2e05b843f3c6980f5bdf0de251dcb3cec12495e`
- Stage: `Phase 37: Targeted Evidence Acquisition Execution v1`
- `300308.SZ`: `tasks_selected=5`, `candidate_chunks_found=15`,
  `semantic_extractions=15`, `eligible_for_persistence=15`,
  `candidates_written=0`, `research_quality_delta=modestly_strengthened`
- `300394.SZ`: `repair_status=partial_repair_dry_run`,
  `after_evidence_chain_count=0`

### Phase 38 Goals

1. Build the `300308.SZ` candidate inventory from Phase 37 dry-run output.
2. Review candidate quality, source traceability, duplicate risk, and sensitive
   variable risk.
3. Build a targeted review queue with dry-run commands only.
4. Persist a capped, low-risk sample through the existing Phase 30 guard.
5. Refresh the `300308.SZ` evidence chain and show before/after evidence count.
6. Revalidate the research packet after persistence while preserving
   `why_not_pending`.
7. Harden `300394.SZ` evidence-chain repair root causes into repair queue tasks.
8. Produce the Phase 38 persistence/review dashboard.

### Phase 38 Guardrails

- Default candidate persistence limit is 5.
- Phase 38 does not fetch new external sources or expand the watchlist.
- Product mix and margin commentary are not upgraded into confirmed ASP.
- Customer allocation proxy is not upgraded into confirmed allocation.
- Internal proxy is not treated as official consensus.
- `usable_for_promotion=false`.
- `promotion_allowed=false`.
- `new_pending_created=0`.
- `paper_order_created=0`.
- No approved paper, paper position, or real trading path is created.
- Raw PDF, raw HTML, text cache, DB, log, and generated HTML artifacts are not
  committed.

### Phase 38 New Artifacts

- `08_scripts/lib/smr_targeted_candidate_inventory.py`
- `08_scripts/lib/smr_targeted_candidate_quality_review.py`
- `08_scripts/reporting/build_phase38_300308_candidate_inventory.py`
- `08_scripts/reporting/build_phase38_300308_candidate_quality_review.py`
- `08_scripts/reporting/build_phase38_300308_targeted_review_queue.py`
- `08_scripts/jobs/persist_phase38_300308_targeted_candidates.py`
- `08_scripts/reporting/build_phase38_300308_evidence_chain_refresh.py`
- `08_scripts/verification/validate_phase38_300308_research_packet_post_persistence.py`
- `08_scripts/reporting/build_phase38_300308_refreshed_packet_after_persistence.py`
- `08_scripts/jobs/upsert_phase38_300394_repair_tasks.py`
- `08_scripts/reporting/build_phase38_300394_repair_queue_summary.py`
- `08_scripts/reporting/build_phase38_persistence_review_dashboard.py`
- `docs/plans/2026-05-24-phase38-targeted-evidence-candidate-review-persistence.md`

### Phase 38 Expected Behavior

For `300308.SZ`, the system should review all 15 candidates, keep sensitive
customer allocation proxy out of confirmed evidence, persist only a capped
guarded sample, and report a strengthened-but-still-not-pending research packet.
For `300394.SZ`, Phase 38 should only harden repair tasks and keep research
deepening disabled until the evidence chain is repaired.

### Phase 38 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase37_execution_dashboard.py --json
python 08_scripts/reporting/build_phase38_300308_candidate_inventory.py --json
python 08_scripts/reporting/build_phase38_300308_candidate_quality_review.py --json
python 08_scripts/reporting/build_phase38_300308_targeted_review_queue.py --json
python 08_scripts/jobs/persist_phase38_300308_targeted_candidates.py --dry-run --json
python 08_scripts/jobs/persist_phase38_300308_targeted_candidates.py --execute --limit 5 --json
python 08_scripts/reporting/build_phase38_300308_evidence_chain_refresh.py --json
python 08_scripts/verification/validate_phase38_300308_research_packet_post_persistence.py --json
python 08_scripts/reporting/build_phase38_300308_refreshed_packet_after_persistence.py --json
python 08_scripts/jobs/upsert_phase38_300394_repair_tasks.py --execute --json
python 08_scripts/reporting/build_phase38_300394_repair_queue_summary.py --json
python 08_scripts/reporting/build_phase38_persistence_review_dashboard.py --json
```

## Phase 37: Targeted Evidence Acquisition Execution v1

Phase 37 executes a small controlled slice of the Phase 36 evidence acquisition
plan. It does not expand the watchlist or chase pending review. The goal is to
test whether existing local sources and text cache can produce safer
quoted-span evidence candidates and whether that makes the `300308.SZ` research
packet modestly stronger.

Current Phase 36 checkpoint:

- Commit: `526991488de3548c051b462585463aa6a2b78276`
- Stage: `Phase 36: Targeted Evidence Acquisition Plan v1`
- `300308.SZ`: `semantic_evidence_total=44`, `critical_gaps=7`,
  `acquisition_tasks=12`, `ASP IR readiness=86`
- `300394.SZ`: `evidence_chain_count=0`, `diagnostic_status=needs_repair`,
  `diagnostic_checks=14`, `recommended_repair_steps=5`
- Phase 36 target remained stronger research packet, not pending review.

### Phase 37 Goals

1. Select 3-5 high-priority `300308.SZ` acquisition tasks.
2. Run targeted source scan against existing real IR sources, text cache,
   semantic evidence, announcements, IR records, news/evidence graph, and
   indexed public commentary.
3. Run deterministic targeted semantic extraction on candidate chunks.
4. Build quoted-span evidence candidates through quality/noise/sensitive guards.
5. Revalidate whether the `300308.SZ` research packet is modestly strengthened.
6. Refresh the `300308.SZ` research packet with before/after evidence impact.
7. Run `300394.SZ` evidence-chain repair dry-run and report root cause.
8. Produce the Phase 37 execution dashboard.

### Phase 37 Guardrails

- Default execution is dry-run.
- Candidate execute is implemented only behind explicit `--execute`.
- Source scan does not perform large external fetching.
- Raw PDF, raw HTML, text cache, DB, log, and generated HTML artifacts are not
  committed.
- OCR is not enabled by default.
- Product mix evidence is not converted into exact ASP.
- Customer demand or order visibility is not converted into confirmed order or
  customer allocation.
- Industry forecast is not treated as company-specific confirmed order.
- Official consensus source availability is not treated as official consensus
  data.
- `usable_for_promotion=false`.
- `new_pending_created=0`.
- `paper_order_created=0`.
- No approved paper, paper position, or real trading path is created.

### Phase 37 New Artifacts

- `08_scripts/lib/smr_controlled_acquisition_selector.py`
- `08_scripts/lib/smr_targeted_source_scan.py`
- `08_scripts/lib/smr_targeted_semantic_extraction.py`
- `08_scripts/lib/smr_targeted_evidence_candidate_builder.py`
- `08_scripts/reporting/build_phase37_controlled_acquisition_selection.py`
- `08_scripts/jobs/run_phase37_targeted_source_scan.py`
- `08_scripts/jobs/run_phase37_targeted_semantic_extraction.py`
- `08_scripts/jobs/build_phase37_targeted_evidence_candidates.py`
- `08_scripts/verification/validate_phase37_300308_post_acquisition_revalidation.py`
- `08_scripts/reporting/build_phase37_300308_refreshed_research_packet.py`
- `08_scripts/jobs/run_phase37_300394_evidence_chain_repair.py`
- `08_scripts/verification/validate_phase37_300394_evidence_chain_repair.py`
- `08_scripts/reporting/build_phase37_execution_dashboard.py`
- `docs/plans/2026-05-24-phase37-targeted-evidence-acquisition-execution.md`

### Phase 37 Expected Behavior

For `300308.SZ`, the system should select a small high-readiness task set,
scan existing local source state, validate quoted spans against chunk text,
build guarded candidate rows, and report a conservative research-quality delta.
The expected outcome is at most `modestly_strengthened` while supplier share,
official consensus, and confirmed customer allocation remain missing.

For `300394.SZ`, the repair job should explain why the evidence chain remains
empty in the current local state. Dry-run repair is successful if it identifies
source/text/cache/persistence root causes without fabricating evidence.

### Phase 37 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase36_evidence_acquisition_dashboard.py --json
python 08_scripts/reporting/build_phase37_controlled_acquisition_selection.py --ticker 300308.SZ --json
python 08_scripts/jobs/run_phase37_targeted_source_scan.py --ticker 300308.SZ --dry-run --json
python 08_scripts/jobs/run_phase37_targeted_semantic_extraction.py --ticker 300308.SZ --dry-run --json
python 08_scripts/jobs/build_phase37_targeted_evidence_candidates.py --ticker 300308.SZ --dry-run --json
python 08_scripts/verification/validate_phase37_300308_post_acquisition_revalidation.py --json
python 08_scripts/reporting/build_phase37_300308_refreshed_research_packet.py --json
python 08_scripts/jobs/run_phase37_300394_evidence_chain_repair.py --dry-run --json
python 08_scripts/verification/validate_phase37_300394_evidence_chain_repair.py --json
python 08_scripts/reporting/build_phase37_execution_dashboard.py --json
```

## Phase 36: Targeted Evidence Acquisition Plan v1

Phase 36 turns the Phase 35 single-stock research packet into a targeted
evidence acquisition plan. It prioritizes `300308.SZ` because its research
packet has partial evidence coverage, while `300394.SZ` first needs a repair
diagnostic because its evidence chain is currently empty in the local state.

Current Phase 35 checkpoint:

- Commit: `602101c467b519699625dfec6ec539c8d33accf3`
- Stage: `Phase 35: Single-Stock Research Packet v1`
- `300308.SZ`: `research_quality=medium_low`, `evidence_coverage=partial`,
  `research_readiness=needs_more_data`
- `300394.SZ`: `research_quality=low`, `evidence_coverage=thin`,
  `research_readiness=needs_more_data`
- `new_pending_created=0`
- `paper_order_created=0`
- No buy/sell, target price, position guidance, or real trading path was
  created.

### Phase 36 Goals

1. Analyze `300308.SZ` targeted evidence gaps.
2. Plan source routes for supplier share, ASP, customer allocation, official
   consensus, shipment/order visibility, industry forecast, and margin/product
   mix evidence.
3. Convert gaps and routes into execution-ready acquisition tasks.
4. Build a focused `300308.SZ` evidence plan that targets stronger research
   quality, not pending review.
5. Diagnose why `300394.SZ` has an empty evidence chain.
6. Build a `300394.SZ` repair plan without writing evidence.
7. Score evidence acquisition readiness by impact, feasibility, source
   availability, expected quality, safety risk, and time cost.
8. Produce the Phase 36 evidence acquisition dashboard.

### Phase 36 Guardrails

- The phase is planning-only.
- No sources are fetched by the acquisition task builders.
- No evidence candidates, lifecycle states, pending review rows, paper orders,
  paper positions, or trades are written.
- Supplier share and customer allocation are not assumed to be publicly
  confirmable.
- ASP is not fabricated from product-mix commentary.
- Internal proxy data is not treated as official consensus.
- `promotion_allowed=false`.
- `new_pending_created=0`.
- `paper_order_created=0`.
- No raw PDF, HTML, text cache, DB, log, or generated HTML artifacts are
  committed.

### Phase 36 New Artifacts

- `08_scripts/lib/smr_targeted_evidence_gap.py`
- `08_scripts/lib/smr_evidence_source_route_planner.py`
- `08_scripts/lib/smr_evidence_acquisition_task.py`
- `08_scripts/lib/smr_evidence_acquisition_readiness.py`
- `08_scripts/lib/smr_evidence_chain_diagnostics.py`
- `08_scripts/reporting/build_phase36_targeted_evidence_gap.py`
- `08_scripts/reporting/build_phase36_evidence_source_routes.py`
- `08_scripts/reporting/build_phase36_evidence_acquisition_tasks.py`
- `08_scripts/reporting/build_phase36_300308_focused_evidence_plan.py`
- `08_scripts/reporting/build_phase36_300394_evidence_chain_diagnostics.py`
- `08_scripts/reporting/build_phase36_300394_evidence_repair_plan.py`
- `08_scripts/reporting/build_phase36_acquisition_readiness_score.py`
- `08_scripts/reporting/build_phase36_evidence_acquisition_dashboard.py`
- `docs/plans/2026-05-24-phase36-targeted-evidence-acquisition-plan.md`

### Phase 36 Expected Behavior

For `300308.SZ`, the system should explain which critical variables still need
evidence, where compliant evidence might be found, what each acquisition task
should produce, and what each task must not infer.

For `300394.SZ`, the system should explain whether the empty evidence chain is
most likely caused by missing sources, missing text cache, semantic extraction
not running, candidate persistence gaps, ticker mapping, or local DB/state
absence. The repair plan remains a dry planning artifact until a separate
approved execution step exists.

### Phase 36 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase35_research_packet_dashboard.py --json
python 08_scripts/reporting/build_phase36_targeted_evidence_gap.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase36_evidence_source_routes.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase36_evidence_acquisition_tasks.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase36_300308_focused_evidence_plan.py --json
python 08_scripts/reporting/build_phase36_300394_evidence_chain_diagnostics.py --json
python 08_scripts/reporting/build_phase36_300394_evidence_repair_plan.py --json
python 08_scripts/reporting/build_phase36_acquisition_readiness_score.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase36_evidence_acquisition_dashboard.py --json
```

## Phase 35: Single-Stock Research Packet v1

Phase 35 starts generating single-stock research work packets for the first
focused ticker set. It does not expand sources, create new governance
frameworks, chase pending review, issue trading instructions, create paper
orders, or relax promotion rules.

Current Phase 34 checkpoint:

- Commit: `45241035d7c3397f7c16fadd46332971e3518058`
- Stage: `Phase 34: Post-Governance Research Revalidation v1`
- `002230.SZ`: `research_weakened`
- `300394.SZ`: `unchanged_needs_more_data`
- `300308.SZ`: `unchanged_needs_more_data`
- `688041.SH`: `unchanged_needs_more_data`
- `confirmed_variables_added=0`
- `new_pending_created=0`
- `paper_order_created=0`

### Phase 35 Goals

1. Build a conservative single-stock thesis for `300394.SZ` and `300308.SZ`.
2. Organize current semantic evidence into an evidence-chain packet.
3. Produce a variable coverage matrix with visible missing variables.
4. Score research quality and readiness without producing an investment rating.
5. Produce bull/base/bear research scenarios without price, return, or position
   guidance.
6. Explain why each ticker is not ready for pending review.
7. Assemble a full single-stock research packet in JSON and Markdown.
8. Produce a two-ticker research packet dashboard.

### Phase 35 Guardrails

- The packet is a research work packet, not an investment memo.
- No buy, sell, add, reduce, target-price, return, or position guidance is
  generated.
- Semantic evidence does not confirm supplier share, ASP, customer allocation,
  or official consensus.
- Internal proxy data is not treated as official consensus.
- `promotion_allowed=false`.
- `new_pending_created=0`.
- `paper_order_created=0`.
- No real trading path is touched.
- Raw PDF, HTML, cache, DB, log, and generated HTML artifacts are not committed.

### Phase 35 New Artifacts

- `08_scripts/lib/smr_single_stock_thesis_builder.py`
- `08_scripts/lib/smr_research_evidence_chain.py`
- `08_scripts/lib/smr_research_quality_scoring.py`
- `08_scripts/reporting/build_phase35_single_stock_thesis.py`
- `08_scripts/reporting/build_phase35_evidence_chain_packet.py`
- `08_scripts/reporting/build_phase35_variable_coverage_matrix.py`
- `08_scripts/reporting/build_phase35_research_quality_score.py`
- `08_scripts/reporting/build_phase35_research_scenarios.py`
- `08_scripts/reporting/build_phase35_why_not_pending.py`
- `08_scripts/reporting/build_phase35_single_stock_research_packet.py`
- `08_scripts/reporting/build_phase35_research_packet_dashboard.py`
- `docs/plans/2026-05-24-phase35-single-stock-research-packet.md`

### Phase 35 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase34_post_governance_research_summary.py --json
python 08_scripts/reporting/build_phase35_single_stock_thesis.py --ticker 300394.SZ --json
python 08_scripts/reporting/build_phase35_evidence_chain_packet.py --ticker 300394.SZ --json
python 08_scripts/reporting/build_phase35_variable_coverage_matrix.py --ticker 300394.SZ --json
python 08_scripts/reporting/build_phase35_research_quality_score.py --ticker 300394.SZ --json
python 08_scripts/reporting/build_phase35_research_scenarios.py --ticker 300394.SZ --json
python 08_scripts/reporting/build_phase35_why_not_pending.py --ticker 300394.SZ --json
python 08_scripts/reporting/build_phase35_single_stock_research_packet.py --ticker 300394.SZ --json
python 08_scripts/reporting/build_phase35_single_stock_research_packet.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase35_research_packet_dashboard.py --json
```

## Phase 34: Post-Governance Research Revalidation v1

Phase 34 feeds the Phase 33 governed evidence state back into the research
system. It does not expand sources, review more evidence at scale, create
pending review rows, produce approved papers, or create any paper or real
orders. Its job is to decide whether each supply-chain pilot ticker's research
state is strengthened, weakened, unchanged and data-starved, ready for a deeper
research packet, or deprioritized.

Current Phase 33 checkpoint:

- Commit: `ee3d9c68160ef2898b1d0c8fd4498f781605ef5a`
- Stage: `Phase 33: Controlled Evidence Review Execution v1`
- `actions_executed=8`
- `audit_records_written=8`
- `lifecycle_status_updated=8`
- `variable_packs_changed=7`
- `expectation_gap_changed=0`
- `valuation_support_changed=0`
- `confirmed_variables_added=0`
- `promotion_allowed_true=0`
- `new_pending_created=0`
- `paper_order_created=0`
- The next step is to revalidate research state from the governed evidence
  rather than push directly toward pending.

### Phase 34 Goals

1. Add post-governance evidence state aggregation.
2. Revalidate variable packs after governed review actions.
3. Revalidate expectation gap confidence conservatively.
4. Revalidate valuation support without replacing official valuation inputs.
5. Revalidate bear case status.
6. Classify ticker-level research state.
7. Produce the next evidence plan.
8. Produce ticker research revalidation packets.
9. Produce the Phase 34 summary dashboard.

### Phase 34 Guardrails

- Reviewed evidence can strengthen or weaken research context, but it cannot
  become promotion evidence by itself.
- Downgraded evidence lowers variable impact.
- Rejected or noisy evidence is excluded from active variable-pack use.
- Supplier share, ASP, customer allocation, and official consensus are not
  fabricated or upgraded to confirmed.
- `ready_for_research_packet` is not `pending_human_review`.
- No buy/sell/add/reduce recommendation is generated.
- `new_pending_created=0`, `paper_order_created=0`, and
  `promotion_allowed_true=0` remain hard safety boundaries.

### Phase 34 New Artifacts

- `08_scripts/lib/smr_post_governance_evidence_state.py`
- `08_scripts/lib/smr_research_state_classifier.py`
- `08_scripts/reporting/build_phase34_post_governance_evidence_state.py`
- `08_scripts/reporting/build_phase34_research_state_classification.py`
- `08_scripts/reporting/build_phase34_next_evidence_plan.py`
- `08_scripts/reporting/build_phase34_research_revalidation_packet.py`
- `08_scripts/reporting/build_phase34_post_governance_research_summary.py`
- `08_scripts/verification/validate_phase34_variable_pack_post_governance.py`
- `08_scripts/verification/validate_phase34_expectation_gap_post_governance.py`
- `08_scripts/verification/validate_phase34_valuation_support_post_governance.py`
- `08_scripts/verification/validate_phase34_bear_case_post_governance.py`
- `docs/plans/2026-05-23-phase34-post-governance-research-revalidation.md`

### Phase 34 Expected Behavior

- Four supply-chain pilot tickers are evaluated:
  `300394.SZ`, `300308.SZ`, `688041.SH`, and `002230.SZ`.
- The summary distinguishes strengthened, weakened, unchanged, and packet-ready
  research states.
- Each ticker gets top missing variables and a targeted next evidence plan.
- Evidence plans remain plan-only and do not write new evidence rows.
- The research revalidation packet clearly separates evidence, assumption,
  missing variables, and promotion boundary.

### Phase 34 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase33_controlled_review_execution_summary.py --json
python 08_scripts/reporting/build_phase34_post_governance_evidence_state.py --json
python 08_scripts/verification/validate_phase34_variable_pack_post_governance.py --json
python 08_scripts/verification/validate_phase34_expectation_gap_post_governance.py --json
python 08_scripts/verification/validate_phase34_valuation_support_post_governance.py --json
python 08_scripts/verification/validate_phase34_bear_case_post_governance.py --json
python 08_scripts/reporting/build_phase34_research_state_classification.py --json
python 08_scripts/reporting/build_phase34_next_evidence_plan.py --json
python 08_scripts/reporting/build_phase34_research_revalidation_packet.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase34_post_governance_research_summary.py --json
```

## Phase 33: Controlled Evidence Review Execution v1

Phase 33 turns the Phase 32 read-only workbench into a guarded execution loop
for a small evidence sample. It does not review all 62 queue items. It executes
only a controlled plan, writes audit records, updates lifecycle status, and
then revalidates sensitive-variable, promotion, pending, paper-order, and
research-impact safety gates.

Current Phase 32 checkpoint:

- Commit: `61e4f6adc7561af3454a3ec65dbb01959b995377`
- Stage: `Phase 32: Evidence Review Workbench v1`
- `workbench_items=62`
- `high_priority=8`
- `sensitive_variable_items=14`
- `download_repair_tasks=3`
- `batch_dry_run_passed=true`
- `promotion_allowed_after_actions=0`
- `new_pending_created=0`
- `paper_order_created=0`
- The next step is to execute a few guarded review actions and verify the real
  audit/lifecycle loop.

### Phase 33 Goals

1. Add controlled review plan builder.
2. Execute guarded review actions on a small sample.
3. Add lifecycle delta report.
4. Add audit log execution verification.
5. Add governance dashboard delta.
6. Add workbench incremental view.
7. Add sensitive guard post-execution revalidation.
8. Add variable pack / expectation gap post-review audit.
9. Add download repair controlled upsert.
10. Add controlled review execution summary.

### Phase 33 Guardrails

- Execute mode uses only the controlled plan.
- Review-only or generated non-persisted items are skipped with a reason.
- Sensitive items are downgraded or sent for better-source review, not approved
  by default.
- `approve_evidence` still does not allow promotion.
- `downgrade_usage` can only reduce usage.
- `reject_evidence` does not physically delete evidence.
- `mark_as_noise` blocks variable-pack usage.
- `request_better_source` creates repair tasks but not evidence.
- No pending review, approved paper, paper order, paper position, or real trade
  is created.
- No semantic evidence is upgraded into confirmed supplier share, confirmed ASP,
  confirmed customer allocation, or official consensus.
- Raw PDF, raw HTML, text cache, DB, logs, and generated files are not
  committed.

### Phase 33 New Artifacts

- `08_scripts/lib/smr_controlled_review_plan.py`
- `08_scripts/reporting/build_phase33_controlled_review_plan.py`
- `08_scripts/jobs/execute_phase33_controlled_review_actions.py`
- `08_scripts/reporting/build_phase33_lifecycle_delta_report.py`
- `08_scripts/verification/validate_phase33_audit_log_execution.py`
- `08_scripts/reporting/build_phase33_governance_delta_dashboard.py`
- `08_scripts/reporting/build_phase33_workbench_incremental_view.py`
- `08_scripts/verification/validate_phase33_sensitive_guard_post_execution.py`
- `08_scripts/verification/validate_phase33_post_review_research_impact.py`
- `08_scripts/verification/validate_phase33_download_repair_upsert.py`
- `08_scripts/reporting/build_phase33_controlled_review_execution_summary.py`
- `docs/plans/2026-05-23-phase33-controlled-evidence-review-execution.md`

### Phase 33 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase32_workbench_summary.py --json
python 08_scripts/reporting/build_phase33_controlled_review_plan.py --json
python 08_scripts/jobs/execute_phase33_controlled_review_actions.py --dry-run --json
python 08_scripts/jobs/execute_phase33_controlled_review_actions.py --execute --json
python 08_scripts/reporting/build_phase33_lifecycle_delta_report.py --json
python 08_scripts/verification/validate_phase33_audit_log_execution.py --json
python 08_scripts/reporting/build_phase33_governance_delta_dashboard.py --json
python 08_scripts/reporting/build_phase33_workbench_incremental_view.py --json
python 08_scripts/verification/validate_phase33_sensitive_guard_post_execution.py --json
python 08_scripts/verification/validate_phase33_post_review_research_impact.py --json
python 08_scripts/jobs/upsert_download_unavailable_repair_tasks.py --execute --limit 3 --json
python 08_scripts/verification/validate_phase33_download_repair_upsert.py --json
python 08_scripts/reporting/build_phase33_controlled_review_execution_summary.py --json
```

## Phase 32: Evidence Review Workbench v1

Phase 32 makes Phase 31 evidence governance usable as a lightweight review
workbench. It does not expand sources, add models, relax promotion, create
pending review, or introduce trading risk. The first version is intentionally
small: JSON/Markdown packets, a static local HTML dashboard, and dry-run command
helpers.

Current Phase 31 checkpoint:

- Commit: `7fdbb16e0bd7ac57470cf2703ae07c64fa709e65`
- Stage: `Phase 31: Evidence Candidate Review Queue + Manual Evidence Governance v1`
- `review_queue_items=62`
- `high_priority=8`
- `sensitive_variable_items=14`
- `download repair tasks=3`
- `promotion_allowed_true=0`
- `new_pending_created=0`
- `sensitive_guard_violations=0`
- `invalid_links=0`
- Evidence governance exists, but it needs a human-usable review surface.

### Phase 32 Goals

1. Add workbench data model.
2. Add priority review packet.
3. Add static local HTML dashboard.
4. Add action command generator.
5. Add batch dry-run review helper.
6. Add review action audit summary.
7. Add download repair workbench.
8. Add workbench summary.
9. Update connector registry conservatively.

### Phase 32 Guardrails

- Workbench items only aggregate data and do not change state.
- Generated commands default to `--dry-run --json`.
- Execute commands are not displayed by default.
- Sensitive variable items display blocked actions.
- `approve_evidence` does not allow promotion.
- Evidence review cannot confirm supplier share, ASP, customer allocation, or
  official consensus.
- Evidence review cannot create pending review.
- Evidence review cannot create approved paper, paper order, paper position, or
  real trades.
- Generated HTML is static and read-only.
- `09_runbooks/generated/` is ignored by git.
- Raw PDF, raw HTML, text cache, DB, logs, and generated HTML are not committed.

### Phase 32 New Artifacts

- `08_scripts/lib/smr_evidence_review_workbench.py`
- `08_scripts/lib/smr_evidence_action_command_generator.py`
- `08_scripts/reporting/build_phase32_priority_review_packet.py`
- `08_scripts/reporting/build_phase32_evidence_review_html.py`
- `08_scripts/reporting/build_phase32_review_action_audit_summary.py`
- `08_scripts/reporting/build_phase32_download_repair_workbench.py`
- `08_scripts/reporting/build_phase32_workbench_summary.py`
- `08_scripts/jobs/run_phase32_batch_review_dry_run.py`
- `docs/plans/2026-05-23-phase32-evidence-review-workbench.md`

### Phase 32 Optional Local Route Decision

The optional local route is not implemented in v1. The static HTML dashboard is
preferred because it is simpler, has no server-side execution surface, requires
no new frontend framework, and cannot trigger review actions from the page.

### Phase 32 Validation Commands

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase31_evidence_governance_dashboard.py --json
python 08_scripts/reporting/build_phase32_priority_review_packet.py --json
python 08_scripts/reporting/build_phase32_priority_review_packet.py --priority high --markdown
python 08_scripts/reporting/build_phase32_evidence_review_html.py --output 09_runbooks/generated/phase32_evidence_review.html
python 08_scripts/jobs/run_phase32_batch_review_dry_run.py --priority high --json
python 08_scripts/reporting/build_phase32_review_action_audit_summary.py --json
python 08_scripts/reporting/build_phase32_download_repair_workbench.py --json
python 08_scripts/reporting/build_phase32_workbench_summary.py --json
python 08_scripts/reporting/build_phase23_connector_availability_dashboard.py --json
```

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
### Phase 47: Paper Watchlist Periodic Review v1

Phase 47 adds periodic review capability to the paper watchlist tracking system
introduced in Phase 46. The system now supports scheduled review state management,
tracking variable snapshots, new evidence delta detection, research-only revalidation,
thesis strength score updates, review execution with audit logging, review packets,
and a periodic review dashboard.

Current Phase 47 checkpoint:

- Commit: (pending)
- Stage: Phase 47: Paper Watchlist Periodic Review & New Evidence Revalidation v1
- 300308.SZ: watchlist tracking continues
- Periodic review executed for 300308.SZ
- Thesis strength score updated
- Dashboard reports reviews_completed >= 1
- pending_created=0
- paper_order_created=0
- real_trade_created=0

#### Phase 47 Goals

1. Periodic review state management.
2. Tracking variable snapshot generation.
3. New evidence delta detection.
4. Research-only new evidence revalidation.
5. Thesis strength score update based on review.
6. Periodic review executor with dry-run/execute modes.
7. Periodic review audit logging.
8. Periodic review packet composition.
9. Periodic review dashboard.

#### Phase 47 Guardrails

- review_due does not mean pending_human_review.
- review_strengthened does not mean buy signal.
- review_weakened does not mean sell signal.
- new_evidence does not auto-trigger pending.
- thesis strength score update is research-only.
- periodic review executor never creates pending/order/trade.
- Audit records always show pending/order/trade = false.
- All scenarios/proxies/unconfirmed remain as-is.
- Promotion rules never relaxed.

#### Phase 47 New Artifacts

Library:
- 08_scripts/lib/smr_paper_watchlist_periodic_review.py
- 08_scripts/lib/smr_tracking_variable_snapshot.py
- 08_scripts/lib/smr_new_evidence_delta_detector.py
- 08_scripts/lib/smr_thesis_strength_score_update.py
- 08_scripts/lib/smr_periodic_review_audit.py

Reporting:
- 08_scripts/reporting/build_phase47_periodic_review_state.py
- 08_scripts/reporting/build_phase47_tracking_variable_snapshot.py
- 08_scripts/reporting/build_phase47_new_evidence_delta.py
- 08_scripts/reporting/build_phase47_thesis_strength_update.py
- 08_scripts/reporting/build_phase47_periodic_review_audit_report.py
- 08_scripts/reporting/build_phase47_periodic_review_packet.py
- 08_scripts/reporting/build_phase47_periodic_review_dashboard.py

Jobs:
- 08_scripts/jobs/run_phase47_periodic_watchlist_review.py

Verification:
- 08_scripts/verification/validate_phase47_new_evidence_revalidation.py

Tests:
- tests/test_phase47_periodic_review_state.py
- tests/test_phase47_tracking_variable_snapshot.py
- tests/test_phase47_new_evidence_delta.py
- tests/test_phase47_new_evidence_revalidation.py
- tests/test_phase47_thesis_strength_update.py
- tests/test_phase47_periodic_review_executor.py
- tests/test_phase47_periodic_review_audit.py
- tests/test_phase47_periodic_review_packet.py
- tests/test_phase47_periodic_review_dashboard.py

#### Next Phase

Phase 48 can extend periodic review with event-driven tracking,
evidence refresh scheduling, or multi-ticker watchlist expansion,
while continuing to enforce: watchlist != pending/order/trade.

### Phase 48: Event-driven Watchlist Evidence Refresh v1

Phase 48 adds event-driven refresh capability. Events are detected from sample fixtures
and existing watchlist state, refresh tasks are generated, evidence refresh is executed,
tracking variables are refreshed, and research-only revalidation is performed.

Current Phase 48 checkpoint:
- Commit: (pending)
- Stage: Phase 48: Event-driven Watchlist Evidence Refresh v1
- 300308.SZ: watchlist tracking continues, event-driven refresh available

#### Phase 48 Goals
1. Event trigger schema with 15 event types
2. Event trigger detector from existing data
3. Event refresh task generation
4. Event evidence refresh executor
5. Event-driven tracking variable refresh
6. Research-only revalidation
7. Event thesis strength update
8. Event trigger audit
9. Event revalidation packet
10. Event watchlist dashboard
11. Windows Unicode-safe output helper

#### Phase 48 Guardrails
- event trigger != pending_human_review
- new evidence != order
- thesis strengthened != buy signal
- sensitive variables never auto-confirmed
- pending/order/trade always = 0

#### Next Phase
Phase 49: expand to multi-ticker watchlist or real-source event detection
with company announcements and IR text monitoring.

### Phase 49: Real Source Event Monitor Pilot v1

Real source metadata from CNINFO (announcements, IR records, annual/quarterly reports, earnings previews) is now
monitored and classified into watchlist events. Events are deduplicated, adapted, and fed into Phase 48 research-only
event refresh.

Current Phase 49 checkpoint:
- Commit: (pending)
- 300308.SZ: real source metadata monitoring enabled

#### Phase 49 Guardrails
- source metadata != evidence
- metadata_only = true, raw_content_saved = false
- network fail -> fixture fallback
- event != pending, metadata != order, source != trade

#### Next Phase
Phase 50: expand to multi-ticker real source monitoring or add financial statement metadata extraction.

### Phase 50: Real Source Text Extraction Evidence Candidate Pilot v1
Metadata -> text availability -> extraction -> normalization -> chunking -> semantic extraction -> candidates -> quality gate -> review queue -> revalidation.
Guard: source!=evidence, candidate!=confirmed, candidate!=pending, raw not committed.

### Phase 51: Real Source Candidate Quality Improvement v1
Candidate quality diagnostics, quoted span validation, source traceability scoring, chunk quality classifier,
quality gate calibration, tracking-support candidate upsert.
Guard: passed_tracking_support!=confirmed, candidate!=pending, no promotion allowed.

### Phase 52: Watchlist Tracking Intelligence Summary v1
Human-readable intelligence summary aggregating Phase 45-51 tracking data. Decision=continue_tracking. Not investment advice.

### Phase 53: Watchlist Daily Brief & Brief Style Contract v1
Daily brief with executive summary + analyst detail, forbidden phrase check, style lint. Not investment advice.


### Phase 54: Research Brief Quality Contract & Investment Logic Upgrade v1
Upgrade from tracking brief to investment logic brief. Business value first, no system status terms.


## Phase 55: Financial Statement Signal Extraction Framework v1

Status: completed

Goals:
- financial metric schema (generic base)
- financial source availability
- financial statement loader (dry-run / execute / fixture-only)
- metric normalization
- quarterly financial signal calculator
- financial signal classifier
- financial-to-thesis impact mapper
- observed-first financial signal brief
- framework generalization report
- dashboard

Design principles:
- Generic base + industry template + single ticker adapter
- Fixture data clearly marked as fixture_only
- Missing data never fabricated
- No AI guessing financial values
- No trading recommendations

Pilot: 300308.SZ
Framework generic capabilities: 6 (schema, availability, loader, normalization, signals, classification)
Industry-specific: 1 (variable mapping)
Not assumed to generalize: 300308-specific thesis claims

Boundary: pending_created=0, paper_order_created=0, real_trade_created=0

## Phase 56: Real Financial Data Source Adapter v1

Status: completed

Goals: source registry, real availability check, structured adapter (akshare/sina), CNINFO fallback, Phase 55 integration, data quality report, real signal recalculation, real financial signal brief, adapter generalization report, dashboard

Design: real structured data priority, fixture for testing only, no AI guessing

Pilot: 300308.SZ via akshare/sina financial report API

Boundary: pending_created=0, paper_order_created=0, real_trade_created=0

## Phase 57: Quarterly Financial Signal Refinement & Multi-ticker Validation v1

Status: in_progress

Goals: capex field matching, cumulative-to-single-quarter conversion, quarterly metric coverage, refined quarterly financial signals, financial signal interpretation, financial thesis impact update, second ticker validation, integrated investment brief, dashboard

Design:
- Cumulative income/cash flow items differenced to single quarter
- Balance sheet items preserved as period-end values
- Capex matched via fuzzy column name search
- Second ticker validates framework generality, not investment thesis
- Financial signals integrated into observed-first investment brief
- No AI guessing financial data
- No automatic attribution of revenue growth to product mix or ASP

Pilot: 300308.SZ
Second ticker validation: 688041.SH (fallback 002230.SZ)
Boundary: pending_created=0, paper_order_created=0, real_trade_created=0

