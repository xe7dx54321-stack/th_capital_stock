# Phase 44 Manual Candidate Review Closeout Implementation Plan

**Goal:** Close the manual evidence intake governance branch by reviewing the three Phase 43 manual candidates, writing lifecycle and audit state, finalizing allowed usage, revalidating research impact, and returning to the 300308.SZ research mainline.

**Architecture:** Phase 44 adds a small lifecycle table and audit table on top of Phase 43 manual candidates. Controlled review actions update only those Phase 44 tables, while reporting scripts compose final usage, research impact, closeout packet, transition plan, dashboard, and read-only HTML.

**Tech Stack:** Python 3.11 scripts, SQLite-backed local state, existing `08_scripts/lib`, `08_scripts/jobs`, `08_scripts/reporting`, `08_scripts/verification`, and `unittest` conventions.

---

### Task 1: Lifecycle and Action Engine

**Files:**
- Create: `08_scripts/lib/smr_manual_candidate_review_lifecycle.py`
- Create: `08_scripts/lib/smr_manual_candidate_review_actions.py`
- Create: `08_scripts/jobs/apply_phase44_manual_candidate_review_action.py`
- Test: `tests/test_phase44_manual_candidate_lifecycle.py`
- Test: `tests/test_phase44_manual_candidate_review_actions.py`

**Steps:**
1. Define manual candidate lifecycle statuses.
2. Map controlled review actions to final lifecycle states.
3. Intercept forbidden actions such as confirmation, promotion, pending, paper order, position, and trade creation.
4. Keep `accept_as_candidate` non-confirming.
5. Keep supplier share scenario-only and customer allocation proxy-only.

### Task 2: Audit and Final Usage

**Files:**
- Create: `08_scripts/lib/smr_manual_candidate_review_audit.py`
- Create: `08_scripts/reporting/build_phase44_manual_candidate_review_audit.py`
- Create: `08_scripts/reporting/build_phase44_manual_candidate_final_usage_matrix.py`
- Test: `tests/test_phase44_manual_candidate_audit.py`
- Test: `tests/test_phase44_final_usage_matrix.py`

**Steps:**
1. Write audit records for every execute review action.
2. Include before/after status, confirmation status, allowed usage, pending/paper/promotion flags.
3. Build final usage rows for official consensus, supplier share, and customer allocation.
4. Verify confirmed variables and promotion-enabled candidates remain zero.

### Task 3: Research Impact and Closeout Packet

**Files:**
- Create: `08_scripts/verification/validate_phase44_manual_candidate_research_impact_closeout.py`
- Create: `08_scripts/reporting/build_phase44_manual_candidate_closeout_packet.py`
- Test: `tests/test_phase44_research_impact_closeout.py`
- Test: `tests/test_phase44_closeout_packet.py`

**Steps:**
1. Validate that all three candidates were reviewed.
2. Report research impact as better bounded but not upgraded.
3. Keep official consensus, supplier share, and customer allocation unconfirmed.
4. Mark manual intake branch status as closed.
5. Set `next_mainline_step=phase45_final_research_packet_review`.

### Task 4: Transition Plan, Dashboard, and HTML

**Files:**
- Create: `08_scripts/reporting/build_phase44_mainline_transition_plan.py`
- Create: `08_scripts/reporting/build_phase44_closeout_dashboard.py`
- Create: `08_scripts/reporting/build_phase44_closeout_html.py`
- Test: `tests/test_phase44_mainline_transition_plan.py`
- Test: `tests/test_phase44_closeout_dashboard.py`
- Test: `tests/test_phase44_closeout_html.py`

**Steps:**
1. Build a transition plan that explicitly closes the manual intake governance branch.
2. Build a dashboard with reviewed count, audit count, branch status, and next mainline step.
3. Generate read-only HTML under `09_runbooks/generated/`.
4. Ensure no trade advice, target price, or position guidance appears.

### Task 5: Validation and Commit

**Files:**
- Modify: `09_runbooks/smr-research-upgrade-progress.md`
- Create: `docs/plans/2026-05-24-phase44-manual-candidate-review-closeout.md`

**Steps:**
1. Run py_compile across scripts.
2. Run all unit tests.
3. Run Phase 3/4/5/6/14 validators.
4. Run Phase 43 dashboard and all Phase 44 commands.
5. Confirm raw/cache/DB/log/generated HTML artifacts are ignored and not staged.
6. Commit with `phase44: close out manual candidate review`.
