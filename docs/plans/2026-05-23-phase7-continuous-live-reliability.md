# Phase 7 Continuous Live Reliability Implementation Plan

**Goal:** Make the Phase 6 live multi-ticker pipeline continuously reproducible, history-aware, and stronger on A/H fundamentals and filing-table extraction without relaxing promotion rules.

**Architecture:** Add a small run-history layer on top of the existing SQLite/task-registry flow, then harden the A/H filing extraction path so more fields resolve with explicit missing reasons. Extend portfolio risk reporting to show current, pending, and risk-adjusted exposure, and keep all candidate sizing decisions ledger-backed and rule-driven.

**Tech Stack:** Python, SQLite, Markdown reports, existing SMR lib/jobs/verification/reporting scripts, `unittest`.

---

### Task 1: Add live run history storage

**Files:**
- Create: `08_scripts/lib/smr_live_run_history.py`
- Modify: `08_scripts/verification/validate_phase6_multi_ticker_live.py`
- Modify: `08_scripts/reporting/build_phase7_live_run_history_summary.py`
- Modify: `tests/test_phase6_live_run_history.py`

**Step 1: Write the failing test**

Create a test that records two synthetic live runs and asserts that the later run can be compared against the previous run.

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_phase6_live_run_history -v`
Expected: fail because the history helper does not exist yet.

**Step 3: Write minimal implementation**

Implement a `phase_live_run_history` table, insert/update helpers, and a `compare_last_run` helper that computes improvement/deterioration and repeated blockers.

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_phase6_live_run_history -v`
Expected: pass.

**Step 5: Commit**

```bash
git add 08_scripts/lib/smr_live_run_history.py 08_scripts/verification/validate_phase6_multi_ticker_live.py 08_scripts/reporting/build_phase7_live_run_history_summary.py tests/test_phase6_live_run_history.py
git commit -m "phase7: add live run history and comparison helpers"
```

### Task 2: Harden Phase 6 validation output

**Files:**
- Modify: `08_scripts/verification/validate_phase6_multi_ticker_live.py`
- Modify: `tests/test_phase6_live_run_history.py`

**Step 1: Write the failing test**

Add assertions for `--save-run-history` and `--compare-last-run` output fields.

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_phase6_live_run_history -v`
Expected: fail on missing summary fields.

**Step 3: Write minimal implementation**

Add CLI flags, persist run history, and expose per-ticker improvement/deterioration plus repeated blockers in JSON output.

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_phase6_live_run_history -v`
Expected: pass.

### Task 3: Harden A/H fundamentals extraction

**Files:**
- Modify: `08_scripts/lib/smr_fundamentals.py`
- Modify: `08_scripts/lib/smr_filing_chunk_selector.py`
- Modify: `tests/test_phase7_fundamentals_ah.py`

**Step 1: Write the failing test**

Add ticker-level checks for `09988.HK`, `00700.HK`, `300308.SZ`, `688041.SH`, and `002230.SZ` with field-level `missing_reason` coverage.

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_phase7_fundamentals_ah -v`
Expected: fail because field-level extraction metadata is not complete.

**Step 3: Write minimal implementation**

Add synonym maps, unit/currency normalization, sanity checks, and per-field extraction metadata for the A/H path.

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_phase7_fundamentals_ah -v`
Expected: pass.

### Task 4: Upgrade portfolio risk v1.5 and exposure summaries

**Files:**
- Modify: `08_scripts/lib/smr_portfolio_risk.py`
- Modify: `08_scripts/lib/smr_recommendation_candidate.py`
- Modify: `08_scripts/reporting/build_paper_portfolio_summary.py`
- Modify: `tests/test_recommendation_candidate.py`

**Step 1: Write the failing test**

Add assertions for projected exposure, risk-adjusted sizing, and downsize/downgrade behavior when theme/sector exposure is near or over limit.

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_recommendation_candidate -v`
Expected: fail until projected exposure is threaded through the risk/candidate path.

**Step 3: Write minimal implementation**

Compute current exposure, pending exposure if all approved, and exposure after risk-adjusted sizing, then feed the results into candidate sizing and ledger metadata.

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_recommendation_candidate -v`
Expected: pass.

### Task 5: Clean runbook and add Phase 7 acceptance

**Files:**
- Modify: `09_runbooks/smr-research-upgrade-progress.md`

**Step 1: Write the failing test**

No code test; check the file structure manually after rewrite.

**Step 2: Write minimal implementation**

Reformat the runbook into normal multiline Markdown, preserve previous phase checkpoints, and add Phase 7 goals plus acceptance criteria.

**Step 3: Verify**

Run: `Select-String -Path 09_runbooks/smr-research-upgrade-progress.md -Pattern 'Phase 7|run history|A/H|projected exposure'`

### Task 6: End-to-end verification

**Files:**
- Verify: `08_scripts/verification/validate_phase3_e2e.py`
- Verify: `08_scripts/verification/validate_phase4_live_e2e.py`
- Verify: `08_scripts/verification/validate_phase5_paper_portfolio_smoke.py`
- Verify: `08_scripts/verification/validate_phase6_multi_ticker_live.py`
- Verify: `08_scripts/reporting/build_phase7_live_run_history_summary.py`

**Step 1: Run the verification set**

Run:

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history
python 08_scripts/reporting/build_phase7_live_run_history_summary.py
```

**Step 2: Expected outcome**

Keep Phase 6 partial pass behavior intact, with run history and A/H field-level gaps visible, but do not relax promotion rules or force new `pending_human_review` items.
