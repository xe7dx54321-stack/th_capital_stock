# Phase 17 Financial Statement Source Chunk Recovery Plan

**Goal:** recover primary financial statement source chunks for HKEX and CNINFO tickers, link those chunks to evidence, and rerun the Phase 16 parsers without loosening promotion gates.

**Baseline:** Phase 16 refined parser failures into table-specific reasons:

- `00700.HK` `shareholders_equity` -> `balance_sheet_not_found`
- `300308.SZ` `revenue` / `gross_profit` -> `income_statement_table_not_found`
- `688041.SH` `revenue` / `gross_profit` -> `income_statement_table_not_found`
- `002230.SZ` unknown thesis diagnostics improved but did not create pending review

## Scope

Phase 17 focuses on source recovery, not new investment logic.

- Discover primary financial statement sources.
- Extract table-like chunks from annual, interim, and quarterly reports.
- Classify chunks as income statement, balance sheet, cash flow, financial highlights, notes, management discussion, or non-financial sections.
- Link recovered chunks to `document_chunks` and `evidence_items`.
- Rerun existing Phase 16 HKEX/CNINFO parsers on recovered chunks.
- Report before/after recovery status for `00700.HK`, `300308.SZ`, and `688041.SH`.

## Non-Goals

- Do not add new complex agents.
- Do not expand the watchlist.
- Do not fabricate extracted values when no source chunk exists.
- Do not allow low-confidence or source-missing fields into promotion evidence.
- Do not auto-create, auto-approve, or route any paper order.
- Do not commit raw PDFs, HTML dumps, or large generated extraction outputs.

## Tasks

### Task 1: Source Discovery

Create `smr_financial_statement_source_discovery.py` and `discover_financial_statement_sources.py`.

- Use the existing HKEX helper for annual/interim/results announcements.
- Use CNINFO announcement search where ticker org hints are available.
- Prefer manifest and existing DB sources before live discovery.
- Rank annual reports above interim, quarterly, and results announcements.
- Emit explicit `financial_statement_source_not_found` when discovery fails.

### Task 2: Chunk Extraction

Create `smr_financial_statement_chunker.py` and `extract_financial_statement_chunks.py`.

- Parse PDF or cached text without saving raw reports to the repo.
- Detect HKEX and CNINFO section headings.
- Require both heading and table-like structure for statement sections.
- Reject contents pages, disclaimers, and management discussion as core statement tables.
- Preserve `source_id`, `source_url`, `published_at`, `chunk_id`, section type, period, currency, and unit.

### Task 3: Evidence Linkage

Create `link_financial_statement_chunks_to_evidence.py`.

- Upsert the primary source into `filing_documents`.
- Upsert statement chunks into `document_chunks`.
- Create evidence items with `source_subtype=financial_statement`.
- Mark full statement sections usable for fundamentals when confidence is sufficient.
- Keep financial highlights supporting-only.

### Task 4: Parser Rerun

Create `validate_phase17_source_chunk_recovery.py`.

- Link recovered chunks first.
- Rerun Phase 15/16 core blocker recovery payloads.
- Count extracted and derived fields only when evidence IDs are present.
- If a chunk is found but a field is still missing, report a refined missing reason instead of broad table-not-found.

### Task 5: Manifest And Summary

Create `00_control/financial_statement_sources.json` and `build_phase17_source_chunk_recovery_summary.py`.

- Manifest stores source metadata only.
- Summary reports sources, chunks, evidence, extracted fields, derived fields, and remaining table-not-found blockers.

## Validation

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase16_parser_thesis_recovery.py --json
python 08_scripts/jobs/discover_financial_statement_sources.py --tickers 00700.HK,300308.SZ,688041.SH --json
python 08_scripts/jobs/extract_financial_statement_chunks.py --tickers 00700.HK,300308.SZ,688041.SH --json
python 08_scripts/jobs/link_financial_statement_chunks_to_evidence.py --ticker 00700.HK --json
python 08_scripts/jobs/link_financial_statement_chunks_to_evidence.py --ticker 300308.SZ --json
python 08_scripts/jobs/link_financial_statement_chunks_to_evidence.py --ticker 688041.SH --json
python 08_scripts/verification/validate_phase17_source_chunk_recovery.py --tickers 00700.HK,300308.SZ,688041.SH --json
python 08_scripts/reporting/build_phase17_source_chunk_recovery_summary.py --json
```
