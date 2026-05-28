# Phase 47 Paper Watchlist Periodic Review & New Evidence Revalidation v1 Implementation Plan

**Goal:** Enable periodic review of paper watchlist entries (300308.SZ) with tracking variable snapshots,
new evidence delta detection, research-only revalidation, thesis strength updates, and a periodic review dashboard.

**Architecture:** Phase 47 adds a periodic review state model, snapshot/delta/revalidation reporting layers,
a review executor job, audit logging, review packet, and dashboard. All operate purely within the research
tracking domain.

**Tech Stack:** Python 3.11 scripts, SQLite-backed local state, 08_scripts/lib, 08_scripts/jobs,
08_scripts/reporting, 08_scripts/verification, and unittest.

---

### Task 1: Periodic Review State

**Files:**
- Create: 08_scripts/lib/smr_paper_watchlist_periodic_review.py
- Create: 08_scripts/reporting/build_phase47_periodic_review_state.py
- Test: tests/test_phase47_periodic_review_state.py

**Steps:**
1. Define review_due/completed/strengthened/weakened/archive_candidate statuses.
2. Support weekly, on_new_evidence, manual, monthly cadences.
3. Build review state object with watchlist status, thesis delta, and safety gates.
4. Ensure review_due != pending, review_strengthened != buy.

### Task 2: Tracking Variable Snapshot

**Files:**
- Create: 08_scripts/lib/smr_tracking_variable_snapshot.py
- Create: 08_scripts/reporting/build_phase47_tracking_variable_snapshot.py
- Test: tests/test_phase47_tracking_variable_snapshot.py

**Steps:**
1. Snapshot all 11 tracking variables from Phase 46 variable definitions.
2. Classify deltas: strengthened, weakened, unchanged_positive, unchanged_gaps, needs_more_evidence.
3. Keep scenario/proxy/unconfirmed labels without promotion.
4. Output summary counts.

### Task 3: New Evidence Delta Detector

**Files:**
- Create: 08_scripts/lib/smr_new_evidence_delta_detector.py
- Create: 08_scripts/reporting/build_phase47_new_evidence_delta.py
- Test: tests/test_phase47_new_evidence_delta.py

**Steps:**
1. Check evidence chain count from semantic_evidence table.
2. Check manual candidate count.
3. Report delta_status: no_new_evidence or new_evidence_detected.
4. no_new_evidence is a valid result; new evidence only triggers research-only revalidation.

### Task 4: New Evidence Research-only Revalidation

**Files:**
- Create: 08_scripts/verification/validate_phase47_new_evidence_revalidation.py
- Test: tests/test_phase47_new_evidence_revalidation.py

**Steps:**
1. Wrapper over delta detector to produce revalidation judgment.
2. no-op when no new evidence.
3. research_only_revalidated when evidence found.
4. Always keeps pending/order/trade at 0.

### Task 5: Thesis Strength Score Update

**Files:**
- Create: 08_scripts/lib/smr_thesis_strength_score_update.py
- Create: 08_scripts/reporting/build_phase47_thesis_strength_update.py
- Test: tests/test_phase47_thesis_strength_update.py

**Steps:**
1. Score can increase (+5 for strengthened) or decrease (-5 for weakened).
2. Bucket transitions at 75, 55, 35 thresholds.
3. Forbidden interpretations: buy_signal, pending_approval, paper_order.

### Task 6: Periodic Watchlist Review Executor

**Files:**
- Create: 08_scripts/jobs/run_phase47_periodic_watchlist_review.py
- Test: tests/test_phase47_periodic_review_executor.py

**Steps:**
1. dry-run reads state without writing.
2. execute writes review state and audit.
3. Idempotent with upsert.
4. Always keeps pending/order/trade at 0.

### Task 7: Periodic Review Audit

**Files:**
- Create: 08_scripts/lib/smr_periodic_review_audit.py
- Create: 08_scripts/reporting/build_phase47_periodic_review_audit_report.py
- Test: tests/test_phase47_periodic_review_audit.py

**Steps:**
1. Dedicated audit table with before/after status and thesis_delta.
2. Write audit on execute.
3. Queryable by ticker.

### Task 8: Periodic Review Packet

**Files:**
- Create: 08_scripts/reporting/build_phase47_periodic_review_packet.py
- Test: tests/test_phase47_periodic_review_packet.py

**Steps:**
1. Composite packet joining state, snapshot, delta, score, and judgment.
2. why_not_pending and forbidden_actions clearly stated.

### Task 9: Periodic Review Dashboard

**Files:**
- Create: 08_scripts/reporting/build_phase47_periodic_review_dashboard.py
- Test: tests/test_phase47_periodic_review_dashboard.py

**Steps:**
1. Summary with entries, reviews_completed, status counts.
2. Ticker rows with score and review status.
3. All pending/order/trade counters = 0.

### Task 10: Documentation and Validation

**Files:**
- Modify: 09_runbooks/smr-research-upgrade-progress.md
- Create: docs/plans/2026-05-24-phase47-paper-watchlist-periodic-review.md

### Task 11: Commit

**Steps:**
1. Run py_compile across script directories.
2. Run full unit tests.
3. Run Phase 3/4/5/6/14/46 validators.
4. Run all Phase 47 commands.
5. Confirm raw/cache/DB/log/generated artifacts not staged.
6. Commit with phase47: add paper watchlist periodic review.
