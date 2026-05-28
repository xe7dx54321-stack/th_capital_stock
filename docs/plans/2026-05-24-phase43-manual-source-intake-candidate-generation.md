# Phase 43 Manual Source Intake Candidate Generation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert bounded manual source intake samples into manual evidence candidates, rejection records, permission audits, review queue items, guarded persistence, dashboard output, and research-impact validation without confirming variables or enabling promotion.

**Architecture:** Phase 43 builds on Phase 42 manual intake validation. It keeps sample payload generation pure, routes valid payloads into a dedicated manual candidate table, routes invalid payloads into rejection records, applies a permission/allowed-usage guard, and reports research impact without touching investment approval or trading paths.

**Tech Stack:** Python 3.11 scripts, SQLite-backed local state, existing `08_scripts/lib`, `08_scripts/jobs`, `08_scripts/reporting`, `08_scripts/verification`, and `unittest` conventions.

---

### Task 1: Manual Intake Payload Samples

**Files:**
- Create: `08_scripts/lib/smr_manual_intake_payload.py`
- Create: `08_scripts/reporting/build_phase43_manual_intake_samples.py`
- Test: `tests/test_phase43_manual_intake_payload.py`

**Steps:**
1. Define deterministic sample payloads for `official_consensus`, `supplier_share`, and `confirmed_customer_allocation`.
2. Include permission status, source metadata, quoted span, requested allowed usage, limitations, and `raw_file_attached=false`.
3. Add an invalid internal consensus proxy fixture for rejection tests.
4. Verify the reporting script emits three valid samples and never writes evidence or pending review.

### Task 2: Candidate Generation and Rejection

**Files:**
- Create: `08_scripts/lib/smr_manual_intake_candidate_generator.py`
- Create: `08_scripts/lib/smr_manual_intake_rejection.py`
- Create: `08_scripts/jobs/build_phase43_manual_intake_candidates.py`
- Create: `08_scripts/reporting/build_phase43_manual_intake_rejection_report.py`
- Test: `tests/test_phase43_manual_intake_candidate_generator.py`
- Test: `tests/test_phase43_rejection_record.py`

**Steps:**
1. Reuse Phase 42 manual intake validation as the first gate.
2. Add Phase 43 guards for missing quoted span, missing provider/date/reference, unauthorized permission, internal proxy official consensus, scenario requesting confirmed supplier share, and proxy requesting confirmed customer allocation.
3. Convert valid payloads into manual candidates with `usable_for_promotion=false` and non-confirmed confirmation statuses.
4. Convert invalid payloads into rejection records with recommended fixes.
5. Support dry-run and guarded execute modes.

### Task 3: Permission Guard and Review Queue

**Files:**
- Create: `08_scripts/lib/smr_manual_intake_permission_guard.py`
- Create: `08_scripts/reporting/build_phase43_manual_intake_permission_audit.py`
- Create: `08_scripts/reporting/build_phase43_manual_intake_review_queue.py`
- Test: `tests/test_phase43_permission_guard.py`
- Test: `tests/test_phase43_manual_intake_review_queue.py`

**Steps:**
1. Calibrate allowed usage for each candidate type.
2. Keep official consensus limited to `expectation_gap_benchmark_if_authorized`.
3. Downgrade supplier-share scenario to `scenario_analysis_only`.
4. Downgrade customer-allocation proxy to `bear_case_context_or_scenario_support`.
5. Build a review queue that allows candidate review/rejection/downgrade but forbids confirmation, promotion, and pending creation.

### Task 4: Guarded Persistence and Research Impact

**Files:**
- Create: `08_scripts/jobs/persist_phase43_manual_intake_candidates.py`
- Create: `08_scripts/verification/validate_phase43_manual_intake_research_impact.py`
- Test: `tests/test_phase43_guarded_persistence.py`
- Test: `tests/test_phase43_research_impact.py`

**Steps:**
1. Persist only candidates that pass the permission guard.
2. Preserve limitations, permission status, quoted span, allowed usage, and confirmation status.
3. Mark persisted candidates without converting them into confirmed evidence.
4. Revalidate research packet impact as better bounded with manual candidates but no confirmed variables, pending review, paper order, or promotion relaxation.

### Task 5: Dashboard, HTML, Validation, and Commit

**Files:**
- Create: `08_scripts/reporting/build_phase43_manual_intake_dashboard.py`
- Create: `08_scripts/reporting/build_phase43_manual_intake_html.py`
- Modify: `09_runbooks/smr-research-upgrade-progress.md`
- Test: `tests/test_phase43_dashboard.py`
- Test: `tests/test_phase43_html.py`

**Steps:**
1. Build a dashboard that separates candidates from confirmed evidence.
2. Generate read-only HTML under `09_runbooks/generated/`, which remains ignored.
3. Run py_compile, unittest, Phase 3/4/5/6/14 validators, Phase 42 dashboard, and all Phase 43 commands.
4. Confirm no raw/cache/DB/log/generated HTML artifacts are staged.
5. Commit with `phase43: generate candidates from manual source intake`.
