# Phase 42 Follow-up Evidence Fulfillment & Manual Source Intake Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a research-only fulfillment layer for Phase 41 follow-up requests, including manual intake templates, validation, scenario/proxy boundaries, packet/dashboard output, and impact revalidation.

**Architecture:** Phase 42 reads Phase 41 specific evidence requests and source-route reports, then classifies fulfillment without writing evidence. Manual intake is template/validation only; supplier share is scenario-only by default; customer allocation is audited as proxy-only unless direct disclosure is validated in a future phase.

**Tech Stack:** Python 3.11 scripts, SQLite-backed local state, unittest, existing `08_scripts/lib` and `08_scripts/reporting` conventions.

---

### Task 1: Follow-up Fulfillment State

**Files:**
- Create: `08_scripts/lib/smr_followup_fulfillment_state.py`
- Create: `08_scripts/reporting/build_phase42_followup_fulfillment_state.py`
- Test: `tests/test_phase42_followup_fulfillment_state.py`

**Steps:**
1. Read Phase 41 specific evidence requests for `official_consensus`, `supplier_share`, and `confirmed_customer_allocation`.
2. Map each request to a conservative fulfillment status.
3. Return request rows with current evidence status, allowed usage, next action, and `can_be_confirmed=false`.
4. Verify `authorized_source_required=1`, `scenario_only=1`, `proxy_only=1`, and `pending_created=0`.

### Task 2: Manual Source Intake

**Files:**
- Create: `08_scripts/lib/smr_manual_source_intake.py`
- Create: `08_scripts/reporting/build_phase42_manual_source_intake_template.py`
- Create: `08_scripts/lib/smr_manual_source_intake_validator.py`
- Create: `08_scripts/jobs/validate_phase42_manual_source_intake.py`
- Test: `tests/test_phase42_manual_source_intake.py`
- Test: `tests/test_phase42_manual_source_intake_validator.py`

**Steps:**
1. Generate evidence-type-specific templates for official consensus, supplier share, and customer allocation.
2. Keep templates format-only with empty `quoted_span`.
3. Validate built-in samples for authorized consensus, supplier-share scenario, and customer-allocation proxy.
4. Reject internal proxy as official consensus.
5. Ensure validator never writes evidence or pending.

### Task 3: Fulfillment Boundaries

**Files:**
- Create: `08_scripts/lib/smr_official_consensus_fulfillment.py`
- Create: `08_scripts/lib/smr_supplier_share_scenario_registry.py`
- Create: `08_scripts/lib/smr_customer_allocation_proxy_audit.py`
- Create reporting wrappers for each module.
- Test: `tests/test_phase42_official_consensus_fulfillment.py`
- Test: `tests/test_phase42_supplier_share_scenario_registry.py`
- Test: `tests/test_phase42_customer_allocation_proxy_audit.py`

**Steps:**
1. Report official consensus as `authorized_source_required` until valid source metadata exists.
2. Build a placeholder supplier-share scenario registry with `is_confirmed=false`.
3. Audit customer-allocation proxy candidates and keep violations at zero.
4. Preserve `pending_created=0`, `paper_order_created=0`, and `promotion_rules_relaxed=false`.

### Task 4: Packet, Dashboard, HTML, and Revalidation

**Files:**
- Create: `08_scripts/reporting/build_phase42_followup_fulfillment_packet.py`
- Create: `08_scripts/verification/validate_phase42_research_packet_impact.py`
- Create: `08_scripts/reporting/build_phase42_fulfillment_dashboard.py`
- Create: `08_scripts/reporting/build_phase42_fulfillment_html.py`
- Test: `tests/test_phase42_followup_fulfillment_packet.py`
- Test: `tests/test_phase42_research_packet_impact.py`
- Test: `tests/test_phase42_fulfillment_dashboard.py`
- Test: `tests/test_phase42_fulfillment_html.py`

**Steps:**
1. Compose the three fulfillment branches into one packet.
2. Revalidate research packet impact as `unchanged_but_better_bounded`.
3. Build dashboard summary and next steps without trade advice.
4. Generate read-only HTML under `09_runbooks/generated/`, which remains ignored.

### Task 5: Validation and Commit

**Files:**
- Modify: `09_runbooks/smr-research-upgrade-progress.md`
- Create: `docs/plans/2026-05-24-phase42-followup-evidence-fulfillment-manual-source-intake.md`

**Steps:**
1. Run `python -m py_compile` across scripts.
2. Run `python -m unittest discover -s tests -v`.
3. Run Phase 3/4/5/6/14 validators.
4. Run all Phase 42 reporting and verification commands.
5. Confirm no raw/cache/DB/log/generated HTML artifacts are staged.
6. Commit with `phase42: add follow-up evidence fulfillment and manual intake`.
