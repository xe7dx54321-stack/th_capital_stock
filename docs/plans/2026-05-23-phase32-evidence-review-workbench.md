# Phase 32 Evidence Review Workbench v1

## Purpose

Phase 32 turns Phase 31 evidence governance into a lightweight human review
workbench. The goal is not to expand sources or add models. The goal is to make
the existing evidence review queue readable, filterable, auditable, and safe to
dry-run.

## Starting Point

Current baseline:

- Commit: `7fdbb16e0bd7ac57470cf2703ae07c64fa709e65`
- Stage: `Phase 31: Evidence Candidate Review Queue + Manual Evidence Governance v1`
- `review_queue_items=62`
- `high_priority=8`
- `sensitive_variable_items=14`
- `total_semantic_evidence=60`
- `linked_to_variable_pack=48`
- `promotion_allowed_true=0`
- `new_pending_created=0`
- `sensitive_guard_violations=0`
- `invalid_links=0`
- `repair_tasks_identified=3`
- `repair_tasks_written=0`
- `audit_records=0`

## Scope

Phase 32 adds:

- Workbench data model.
- Priority review packet.
- Static local HTML review dashboard.
- Safe dry-run action command generator.
- Batch dry-run helper.
- Review action audit summary.
- Download repair workbench packet.
- Workbench governance summary.
- Connector registry update.

## Non-Goals

Phase 32 does not:

- Add a frontend framework.
- Add a permission system.
- Expand the watchlist.
- Expand source extraction.
- Execute review actions by default.
- Show execute commands by default.
- Enable promotion.
- Create pending review.
- Create paper orders or positions.
- Trigger real trades.
- Commit generated HTML, raw PDFs, raw HTML, text cache, DB, or logs.

## Design

The workbench is a read-only aggregation layer:

1. Load Phase 31 review queue items.
2. Merge lifecycle, sensitive-variable guard, source, quality, and link metadata.
3. Generate conservative recommended actions.
4. Attach dry-run commands only.
5. Render JSON, Markdown, and static HTML views.
6. Run batch dry-run checks through the existing Phase 31 guarded action runner.

Sensitive variable items never recommend direct confirmed upgrades. They are
shown with blocked actions such as `upgrade_to_confirmed_customer_allocation`,
`upgrade_to_confirmed_supplier_share`, `upgrade_to_confirmed_ASP`,
`upgrade_to_official_consensus`, and `allow_promotion`.

## Optional Local Route Decision

The optional local route is not implemented in v1. A static generated HTML file
is safer for the first workbench because it has no server-side action surface,
requires no new frontend dependency, and cannot execute review actions from the
page. The generated output path is `09_runbooks/generated/`, which is ignored by
git.

## Validation

Core validation commands:

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/reporting/build_phase32_priority_review_packet.py --json
python 08_scripts/reporting/build_phase32_priority_review_packet.py --priority high --markdown
python 08_scripts/reporting/build_phase32_evidence_review_html.py --output 09_runbooks/generated/phase32_evidence_review.html
python 08_scripts/jobs/run_phase32_batch_review_dry_run.py --priority high --json
python 08_scripts/reporting/build_phase32_review_action_audit_summary.py --json
python 08_scripts/reporting/build_phase32_download_repair_workbench.py --json
python 08_scripts/reporting/build_phase32_workbench_summary.py --json
python 08_scripts/reporting/build_phase23_connector_availability_dashboard.py --json
```

## Safety Invariants

- `promotion_allowed_true=0`
- `new_pending_created=0`
- `paper_order_created=0`
- Execute commands are not displayed by default.
- Workbench reports do not mutate lifecycle state.
- Batch dry-run rolls back state.
- Generated HTML is ignored by git.
