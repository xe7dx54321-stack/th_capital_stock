# Phase 45 Final Research Packet Review Implementation Plan

**Goal:** Return from manual evidence governance to the 300308.SZ research mainline and produce a final research packet review that can classify paper watchlist readiness without creating pending, orders, or trading actions.

**Architecture:** Phase 45 is a read-only composition layer. It aggregates Phase 35-44 research assets, reviews thesis validity, evidence sufficiency, variable coverage, expectation-gap boundaries, bear case pressure, and classifies paper watchlist tracking readiness while keeping promotion and trading boundaries closed.

**Tech Stack:** Python 3.11 scripts, existing SQLite-backed local state, `08_scripts/lib`, `08_scripts/reporting`, and `unittest`.

---

### Task 1: Final Research Asset Summary

**Files:**
- Create: `08_scripts/lib/smr_final_research_asset_aggregator.py`
- Create: `08_scripts/reporting/build_phase45_final_research_asset_summary.py`
- Test: `tests/test_phase45_final_asset_summary.py`

**Steps:**
1. Aggregate completed Phase 35-44 research stages.
2. Summarize evidence-chain counts and manual candidate closeout.
3. Keep manual candidates separate from confirmed evidence.
4. Surface remaining core gaps.

### Task 2: Thesis and Evidence Reviews

**Files:**
- Create: `08_scripts/lib/smr_final_thesis_review.py`
- Create: `08_scripts/reporting/build_phase45_final_thesis_review.py`
- Create: `08_scripts/reporting/build_phase45_final_evidence_sufficiency_review.py`
- Test: `tests/test_phase45_final_thesis_review.py`
- Test: `tests/test_phase45_evidence_sufficiency.py`

**Steps:**
1. Classify thesis as research-supported but not investment-ready.
2. Separate research conclusion readiness from investment pending readiness.
3. Keep thesis confidence below high.
4. Confirm no trade advice is emitted.

### Task 3: Variable, Valuation, and Bear Case Reviews

**Files:**
- Create: `08_scripts/reporting/build_phase45_final_variable_coverage_review.py`
- Create: `08_scripts/reporting/build_phase45_expectation_gap_valuation_boundary.py`
- Create: `08_scripts/reporting/build_phase45_final_bear_case_review.py`
- Test: `tests/test_phase45_variable_coverage.py`
- Test: `tests/test_phase45_expectation_gap_valuation.py`
- Test: `tests/test_phase45_bear_case_review.py`

**Steps:**
1. Split variables into supported, partial, scenario-only, proxy-only, and missing/unconfirmed.
2. Keep supplier share scenario-only and customer allocation proxy-only.
3. Keep official consensus unconfirmed.
4. Keep valuation and expectation-gap conclusions scenario-bound.
5. Keep bear case partially mitigated but not cleared.

### Task 4: Conclusion, Watchlist Readiness, Packet, and Dashboard

**Files:**
- Create: `08_scripts/lib/smr_final_research_conclusion.py`
- Create: `08_scripts/reporting/build_phase45_final_research_conclusion.py`
- Create: `08_scripts/reporting/build_phase45_paper_watchlist_readiness_packet.py`
- Create: `08_scripts/reporting/build_phase45_final_research_packet.py`
- Create: `08_scripts/reporting/build_phase45_final_review_dashboard.py`
- Test: `tests/test_phase45_final_research_conclusion.py`
- Test: `tests/test_phase45_paper_watchlist_readiness.py`
- Test: `tests/test_phase45_final_research_packet.py`
- Test: `tests/test_phase45_final_review_dashboard.py`

**Steps:**
1. Classify 300308.SZ as a paper watchlist candidate if evidence remains bounded.
2. Make paper watchlist tracking distinct from pending human review.
3. Build the full final research packet.
4. Build the Phase 45 final review dashboard pointing to Phase 46.

### Task 5: Validation and Commit

**Files:**
- Modify: `09_runbooks/smr-research-upgrade-progress.md`
- Create: `docs/plans/2026-05-24-phase45-final-research-packet-review.md`

**Steps:**
1. Run py_compile across script directories.
2. Run full unit tests.
3. Run Phase 3/4/5/6/14 validators.
4. Run Phase 44 dashboard and all Phase 45 commands.
5. Confirm raw/cache/DB/log/generated artifacts are not staged.
6. Commit with `phase45: add final research packet review`.
