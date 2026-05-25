# Phase 16 Parser Thesis Recovery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Recover HKEX/CNINFO parser coverage and harden unknown-thesis metadata without loosening promotion gates.

**Architecture:** Phase 16 adds focused parser helpers for HKEX balance sheets and CNINFO income statements, then wires their results into existing fundamentals recovery diagnostics. Unknown thesis handling remains advisory through a dry-run metadata patch and after-patch simulation.

**Tech Stack:** Python, SQLite, existing SMR decision/fundamentals/validator scripts, `unittest`.

---

### Task 1: HKEX Balance Sheet Parser

**Files:**
- Create: `08_scripts/lib/smr_hkex_table_parser.py`
- Test: `tests/test_phase16_hkex_balance_sheet_parser.py`

**Steps:**
- Detect English, Traditional Chinese, Simplified Chinese balance sheet titles.
- Extract shareholders/owners equity using explicit synonyms.
- Prefer owners/shareholders equity over total equity.
- Treat total equity and net assets as fallback.
- Block non-controlling interests and ambiguous fallback samples.

### Task 2: CNINFO Income Statement Parser

**Files:**
- Create: `08_scripts/lib/smr_cninfo_table_parser.py`
- Test: `tests/test_phase16_cninfo_income_statement_parser.py`

**Steps:**
- Detect consolidated income statement and financial metrics sections.
- Extract revenue and operating cost with unit normalization.
- Extract direct gross profit when present.
- Derive gross profit from revenue minus operating cost when both inputs have evidence IDs.
- Mark parent-company-only values as context-only.

### Task 3: Recovery Integration

**Files:**
- Modify: `08_scripts/lib/smr_financial_table_extraction.py`
- Modify: `08_scripts/verification/validate_phase15_core_blocker_recovery.py`

**Steps:**
- Run HKEX parser when H-share shareholders equity is missing.
- Run CNINFO parser when A-share revenue or gross profit is missing.
- Preserve blocked status for source-missing or low-confidence fields.
- Refine broad missing reasons into parser-specific reasons.

### Task 4: Thesis Metadata Hardening

**Files:**
- Modify: `08_scripts/lib/smr_thesis_inference.py`
- Modify: `08_scripts/reporting/build_phase15_unknown_thesis_diagnostics.py`
- Create: `08_scripts/jobs/apply_watchlist_metadata_patch.py`
- Test: `tests/test_phase16_unknown_thesis_metadata.py`

**Steps:**
- Let inference consume `theme_tags`, `business_driver`, `candidate_thesis_hints`, `claim_keywords`, and `proxy_signal_hints`.
- Produce a suggested 002230.SZ metadata patch.
- Simulate after-patch thesis confidence.
- Keep `allow_pending=false`; evidence gates still decide later.

### Task 5: Validator And Summary

**Files:**
- Create: `08_scripts/verification/validate_phase16_parser_thesis_recovery.py`
- Create: `08_scripts/reporting/build_phase16_parser_recovery_summary.py`
- Test: `tests/test_phase16_parser_thesis_recovery_validator.py`
- Test: `tests/test_phase16_parser_recovery_summary.py`

**Steps:**
- Summarize before/after for 00700.HK, 300308.SZ, 688041.SH, and 002230.SZ.
- Count repaired and refined core blockers separately.
- Report unknown thesis before/after simulation.
- Confirm no new pending recommendation is created.

### Task 6: Verification

**Commands:**

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase16_parser_thesis_recovery.py --json
python 08_scripts/reporting/build_phase16_parser_recovery_summary.py --json
python 08_scripts/jobs/apply_watchlist_metadata_patch.py --ticker 002230.SZ --dry-run
```

**Safety checks:**
- No promotion threshold is loosened.
- No real trade path is added.
- No paper order is created from pending review.
- Unknown thesis remains blocked from pending until normal gates pass.
