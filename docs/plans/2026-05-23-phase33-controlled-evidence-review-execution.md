# Phase 33 Controlled Evidence Review Execution v1

## Context

Phase 32 created a readable evidence review workbench with JSON, Markdown,
HTML, dry-run command generation, batch dry-run, audit summary, download repair
workbench, and workbench summary. The workbench is safe and useful, but it is
still mostly read-only: audit records remain empty until guarded execute
actions are run.

Phase 33 executes a small controlled sample from the workbench and validates the
full governance loop:

- controlled review plan
- guarded action execution
- audit log write
- lifecycle status update
- lifecycle delta report
- governance delta dashboard
- workbench incremental view
- sensitive guard post-execution revalidation
- variable pack / expectation gap post-review impact check
- download repair task controlled upsert

## Scope

The first execution sample is intentionally small: 5 to 8 evidence items. The
plan favors high-priority and sensitive-variable items, but only executes
persisted semantic evidence. Review-only generated items are skipped and remain
auditable through skip reasons.

The sample covers:

- sensitive item `downgrade_usage`
- non-sensitive `approve_evidence`
- weak evidence `downgrade_usage`
- `request_better_source`
- `reject_evidence`
- `mark_as_noise`

## Guardrails

Phase 33 does not expand sources, watchlists, models, or extraction range. It
does not approve all high-priority items and does not review all 62 workbench
items.

Every execute action must use the Phase 31 guarded action API. The executor
must not write lifecycle or audit rows through a separate bypass path.

Required safety invariants:

- `usable_for_promotion` remains false.
- `promotion_allowed_true=0`.
- `new_pending_created=0`.
- `paper_order_created=0`.
- no approved paper, paper order, paper position, or real trade is created.
- no semantic evidence becomes confirmed supplier share, confirmed ASP,
  confirmed customer allocation, or official consensus.
- rejected and noisy evidence is not physically deleted.
- download repair tasks do not bypass download controls and do not enable OCR
  by default.

## Implementation

New core module:

- `08_scripts/lib/smr_controlled_review_plan.py`

New reporting scripts:

- `08_scripts/reporting/build_phase33_controlled_review_plan.py`
- `08_scripts/reporting/build_phase33_lifecycle_delta_report.py`
- `08_scripts/reporting/build_phase33_governance_delta_dashboard.py`
- `08_scripts/reporting/build_phase33_workbench_incremental_view.py`
- `08_scripts/reporting/build_phase33_controlled_review_execution_summary.py`

New job:

- `08_scripts/jobs/execute_phase33_controlled_review_actions.py`

New validators:

- `08_scripts/verification/validate_phase33_audit_log_execution.py`
- `08_scripts/verification/validate_phase33_sensitive_guard_post_execution.py`
- `08_scripts/verification/validate_phase33_post_review_research_impact.py`
- `08_scripts/verification/validate_phase33_download_repair_upsert.py`

Modified existing behavior:

- `08_scripts/jobs/upsert_download_unavailable_repair_tasks.py` accepts
  `--limit` for controlled repair task upserts.
- The Phase 32 workbench data model exposes reviewed and remaining counts after
  lifecycle changes.

## Commands

```bash
python 08_scripts/reporting/build_phase33_controlled_review_plan.py --json
python 08_scripts/reporting/build_phase33_controlled_review_plan.py --markdown
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

## Expected Result

After execute, the system can answer:

- which evidence items were reviewed
- which actions were executed
- which audit records were written
- how lifecycle state changed
- which high-priority and sensitive items remain
- whether sensitive variables were wrongly confirmed
- whether promotion, pending review, paper order, or real trade paths stayed
  closed

Phase 33 succeeds when the governance loop is executed and revalidated, not
when new investment recommendations or pending reviews are created.
