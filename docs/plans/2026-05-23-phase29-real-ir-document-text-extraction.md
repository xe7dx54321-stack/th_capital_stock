# Phase 29 Real IR Document Text Extraction v1

## Goal

Turn real IR source metadata into auditable clean text that can be chunked,
semantically extracted, gated, and persisted as evidence candidates with valid
`quoted_span`.

## Scope

- Add document text extraction schema and quality statuses.
- Extract clean text from local PDF / HTML / text sources.
- Keep OCR disabled by default.
- Cache only clean text in ignored generated paths.
- Split extracted IR text into supply-chain-relevant sections.
- Feed extracted text into Phase 28 semantic pipeline and persistence.
- Keep promotion, pending, paper order, and real-trade gates unchanged.

## Implementation

New core modules:

- `08_scripts/lib/smr_document_text_extraction.py`
- `08_scripts/lib/smr_document_text_extractor.py`
- `08_scripts/lib/smr_text_cache.py`
- `08_scripts/lib/smr_ir_section_splitter.py`

New commands:

- `08_scripts/jobs/extract_real_ir_document_text.py`
- `08_scripts/verification/validate_phase29_text_extraction_semantic_evidence.py`
- `08_scripts/reporting/build_phase29_text_extraction_summary.py`

Modified integration:

- `smr_real_ir_document_loader.py` can read text cache and skip metadata-only
  sources.
- `smr_semantic_document_chunker.py` preserves section metadata.
- `build_semantic_ir_evidence.py` supports `--use-text-cache`.
- `persist_semantic_evidence_candidates.py` supports `--use-text-cache`.
- Phase 28 validators can optionally re-use text cache.

## Safety Rules

- Do not submit raw PDF or raw HTML.
- Do not use metadata as body text.
- Do not default to OCR.
- Do not fabricate `quoted_span`.
- Do not let semantic evidence alone create pending review.
- Do not loosen promotion rules.

## Verification

Required:

- `python -m py_compile ...`
- `python -m unittest discover -s tests -v`
- Phase 3 / 4 / 5 / 6 / 14 regression validators.
- Phase 28 real IR semantic summary.
- Phase 29 extraction, semantic re-run, persistence dry-run, revalidation,
  summary, and connector dashboard.
