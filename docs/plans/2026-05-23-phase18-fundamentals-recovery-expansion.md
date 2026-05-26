# Phase 18 Fundamentals Recovery Expansion Plan

**Goal:** close the remaining `688041.SH` source gap and move recovered financial statement fields into fundamentals snapshots and the thesis-aware core blocker gate.

**Baseline:** Phase 17 proved the source -> chunk -> evidence -> parser path for `00700.HK` and `300308.SZ`, while `688041.SH` remained blocked at `financial_statement_source_not_found`.

## Scope

- Resolve CNINFO identity for `688041.SH`.
- Discover and cache the latest usable CNINFO financial statement source.
- Extract and link financial statement chunks for `688041.SH`.
- Recover `688041.SH` `revenue` and `gross_profit` when evidence supports it.
- Update fundamentals snapshots from recovered chunks for `00700.HK`, `300308.SZ`, and `688041.SH`.
- Let thesis-aware missing-field logic ignore recovered fields only when they have evidence IDs and sufficient confidence.
- Add Phase 18 revalidation and daily summary scripts.

## Non-Goals

- Do not add new complex agents.
- Do not expand `ai_core`.
- Do not fabricate fields when source/chunk/evidence is absent.
- Do not loosen promotion rules.
- Do not auto approve pending items.
- Do not create paper orders or paper positions.
- Do not commit raw PDFs, HTML dumps, or generated report outputs.

## Tasks

### Task 1: CNINFO Source Identity

Create `smr_cninfo_source_identity.py` and `resolve_cninfo_source_identity.py`.

- Add curated/manifest identity for `688041.SH`.
- Prefer manifest identity when present.
- Return `cninfo_org_id_missing` for unresolved CN tickers.
- Feed identity hints into financial statement source discovery.

### Task 2: 688041 Source And Chunk Recovery

Extend financial statement source discovery and chunker behavior.

- Select full annual reports over annual report summaries.
- Add manifest source metadata for `688041.SH`.
- Preserve statement heading classification when a section window has already been matched.
- Link recovered `income_statement`, `balance_sheet`, and `cash_flow_statement` chunks to evidence.

### Task 3: Recovered Fundamentals Snapshot Update

Create `smr_recovered_fundamentals.py` and `update_fundamentals_from_recovered_chunks.py`.

- Extract recovered fields directly from financial statement chunks.
- Require `source_evidence_id` for extracted fields.
- Require `input_evidence_ids` for derived fields.
- Preserve previous field value/detail metadata.
- Insert a new fundamentals snapshot rather than mutating old snapshots.

### Task 4: Core Blocker Gate Integration

Update Phase 14 missing-field merge logic.

- Remove a Phase 6 missing field only when the latest fundamentals snapshot has a recovered value, evidence lineage, confidence >= 0.6, and allowed usage above context-only.
- Keep low-confidence recovered fields blocking.
- Do not change promotion thresholds.

### Task 5: Validators And Summary

Create Phase 18 validation and reporting scripts.

- `validate_phase18_remaining_source_gap_closure.py`
- `validate_phase18_fundamentals_recovery_revalidation.py`
- `build_phase18_fundamentals_recovery_summary.py`

## Validation

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/jobs/resolve_cninfo_source_identity.py --ticker 688041.SH --json
python 08_scripts/jobs/discover_financial_statement_sources.py --ticker 688041.SH --json
python 08_scripts/jobs/extract_financial_statement_chunks.py --ticker 688041.SH --json
python 08_scripts/jobs/link_financial_statement_chunks_to_evidence.py --ticker 688041.SH --json
python 08_scripts/verification/validate_phase18_remaining_source_gap_closure.py --ticker 688041.SH --json
python 08_scripts/jobs/update_fundamentals_from_recovered_chunks.py --tickers 00700.HK,300308.SZ,688041.SH --json
python 08_scripts/verification/validate_phase18_fundamentals_recovery_revalidation.py --tickers 00700.HK,300308.SZ,688041.SH --json
python 08_scripts/reporting/build_phase18_fundamentals_recovery_summary.py --json
```
