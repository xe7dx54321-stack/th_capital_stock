# Phase 46 Paper Watchlist Tracking Implementation Plan

**Goal:** Move `300308.SZ` from final research conclusion into research-only paper watchlist tracking without creating pending human review, paper orders, positions, or trades.

**Architecture:** Phase 46 adds a standalone watchlist tracking layer with dedicated entry and audit tables. Reporting scripts compose entry state, tracking variables, triggers, thesis strength, review packet, and dashboard while jobs only upsert watchlist state and audit records.

**Tech Stack:** Python 3.11 scripts, SQLite-backed local state, `08_scripts/lib`, `08_scripts/jobs`, `08_scripts/reporting`, `08_scripts/verification`, and `unittest`.

---

### Task 1: Paper Watchlist Entry and Lifecycle

**Files:**
- Create: `08_scripts/lib/smr_paper_watchlist_entry.py`
- Create: `08_scripts/lib/smr_paper_watchlist_lifecycle.py`
- Create: `08_scripts/reporting/build_phase46_paper_watchlist_entry.py`
- Test: `tests/test_phase46_paper_watchlist_entry.py`
- Test: `tests/test_phase46_watchlist_lifecycle.py`

**Steps:**
1. Define the Phase 46 watchlist entry schema.
2. Keep watchlist status separate from pending, approved paper, order, position, and real trade states.
3. Allow research-only lifecycle transitions.
4. Block forbidden investment or trading states.

### Task 2: Tracking Variables and Triggers

**Files:**
- Create: `08_scripts/lib/smr_paper_watchlist_tracking_variables.py`
- Create: `08_scripts/lib/smr_paper_watchlist_triggers.py`
- Create: `08_scripts/reporting/build_phase46_tracking_variables.py`
- Create: `08_scripts/reporting/build_phase46_tracking_triggers.py`
- Test: `tests/test_phase46_tracking_variables.py`
- Test: `tests/test_phase46_tracking_triggers.py`

**Steps:**
1. Define product mix, order visibility, shipment, ASP proxy, supplier share scenario, official consensus status, customer allocation proxy, bear case risk, valuation boundary, evidence quality, and thesis strength variables.
2. Add strengthening and weakening signals for each variable.
3. Define research-only trigger conditions.
4. Keep trigger actions limited to status update, revalidation request, or archive.

### Task 3: Upsert, Status Update, and Audit

**Files:**
- Create: `08_scripts/lib/smr_paper_watchlist_audit.py`
- Create: `08_scripts/jobs/upsert_phase46_paper_watchlist_entry.py`
- Create: `08_scripts/jobs/update_phase46_watchlist_status.py`
- Create: `08_scripts/reporting/build_phase46_watchlist_audit_report.py`
- Create: `08_scripts/verification/validate_phase46_watchlist_status_update.py`
- Test: `tests/test_phase46_watchlist_upsert.py`
- Test: `tests/test_phase46_watchlist_audit.py`
- Test: `tests/test_phase46_watchlist_status_update.py`

**Steps:**
1. Add an idempotent watchlist upsert job.
2. Write audit records for entry creation and status updates.
3. Allow status updates such as `tracking_strengthened` without promotion.
4. Validate audit and current entry state keep pending, order, and trade counters at zero.

### Task 4: Thesis Score, Review Packet, and Dashboard

**Files:**
- Create: `08_scripts/lib/smr_thesis_strength_tracking.py`
- Create: `08_scripts/reporting/build_phase46_thesis_strength_score.py`
- Create: `08_scripts/reporting/build_phase46_paper_watchlist_review_packet.py`
- Create: `08_scripts/reporting/build_phase46_paper_watchlist_dashboard.py`
- Test: `tests/test_phase46_thesis_strength_score.py`
- Test: `tests/test_phase46_watchlist_review_packet.py`
- Test: `tests/test_phase46_watchlist_dashboard.py`

**Steps:**
1. Score thesis strength conservatively as research tracking only.
2. Explain why tracking does not equal pending.
3. Build a review packet with variables, triggers, score, and forbidden actions.
4. Build a dashboard that counts the active tracking family while preserving current status.

### Task 5: Documentation, Validation, and Commit

**Files:**
- Modify: `09_runbooks/smr-research-upgrade-progress.md`
- Create: `docs/plans/2026-05-24-phase46-paper-watchlist-tracking.md`

**Steps:**
1. Run py_compile across script directories.
2. Run full unit tests.
3. Run Phase 3/4/5/6/14 validators.
4. Run Phase 45 dashboard and all Phase 46 commands.
5. Confirm raw/cache/DB/log/generated artifacts are not staged.
6. Commit with `phase46: add paper watchlist tracking`.
