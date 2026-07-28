# Stock Deep Dive V3 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an evidence-backed, long-form stock research workflow that plans, retrieves, analyzes, synthesizes, validates, and persists a useful Chinese report.

**Architecture:** Extend the existing Python governed packet with a backward-compatible `research_v3` domain, then let the Node model gateway synthesize and repair the final report. Keep deterministic fallback output and artifact/audit persistence so model failure never destroys the research result.

**Tech Stack:** Python 3.11, SQLite, Node.js/Express, MiniMax-compatible LLM gateway, React/Vitest, unittest/pytest, node:test.

---

### Task 1: Freeze V3 contracts and quality criteria

**Files:**
- Create: `docs/plans/2026-07-21-stock-deep-dive-v3-spec.md`
- Create: `docs/adr/0003-stock-deep-dive-v3-staged-governed-synthesis.md`
- Test: `tests/workflows/test_stock_deep_dive_v3.py`

**Steps:**
1. Write tests for the plan, provider status, corpus, graph, instruments, analysis, coverage and audit artifact.
2. Run the focused test and verify it fails because V3 fields do not exist.
3. Implement only the V3 contract builders.
4. Run the focused test and require PASS.

### Task 2: Implement source-aware research collection

**Files:**
- Create: `smr_app/research/research_plan_v3.py`
- Create: `smr_app/adapters/research_context_v3.py`
- Modify: `smr_app/workflows/stock_deep_dive.py`
- Test: `tests/workflows/test_stock_deep_dive_v3.py`

**Steps:**
1. Add fixture tables for filing documents, chunks, news, events, sector config, pool and daily bars.
2. Verify the collection tests fail.
3. Implement table capability checks and bounded deterministic queries.
4. Verify missing tables degrade a branch rather than fail the run.
5. Verify the focused suite passes.

### Task 3: Implement deterministic research analysis and fallback report

**Files:**
- Create: `smr_app/research/analysis_v3.py`
- Create: `smr_app/research/report_v3.py`
- Modify: `smr_app/workflows/stock_deep_dive.py`
- Test: `tests/workflows/test_stock_deep_dive_v3.py`

**Steps:**
1. Write failing tests for financial trend extraction, section coverage, citations, risk signals and system-noise exclusion.
2. Implement generic annual-report key-metric extraction and derived ratios.
3. Implement the structured deterministic report with all standard sections.
4. Run V2 and V3 workflow tests; both must pass.

### Task 4: Implement governed model synthesis and repair

**Files:**
- Create: `api/services/stock-research-v3-service.js`
- Modify: `api/services/governed-workflow-runner.js`
- Modify: `api/app.js`
- Test: `tests/api/stock-research-v3.test.js`

**Steps:**
1. Write failing tests for prompt constraints, unknown citations, required sections, minimum useful length, repair and deterministic fallback.
2. Implement a two-call maximum synthesis service using the existing model gateway.
3. Persist a passing model report over the draft artifact and attach validation metadata.
4. Keep the governed draft when the model is unavailable or fails validation.
5. Run API tests and require PASS.

### Task 5: Separate report from execution metadata in the UI/API

**Files:**
- Modify: `api/services/chat-enhanced-service.js`
- Modify: `src/features/chat/ChatPanel.tsx`
- Modify: `src/app/workbench.css`
- Test: `tests/api/governed-stock-chat.test.js`
- Test: `src/features/workflows/__tests__/ResearchWorkbench.test.tsx`

**Steps:**
1. Write tests proving execution metadata is not appended to the report body.
2. Return execution and artifacts as structured metadata.
3. Render metadata in a collapsible research-process panel.
4. Run UI tests and visually inspect the workbench.

### Task 6: Real-data quality evaluation

**Files:**
- Create: `tools/evaluate_stock_deep_dive_v3.py`
- Create: `config/stock_deep_dive_v3_eval.json`
- Modify: `scripts/check.ps1`

**Steps:**
1. Run all focused Python, API and UI tests.
2. Run V3 against the real source database for `300308.SZ`.
3. Inspect the report for the specified annual-report facts and section coverage.
4. Run at least three cross-industry regression tickers.
5. Fix failures and repeat until quality gates pass.
6. Run `npm run check:full` as the final regression gate.
