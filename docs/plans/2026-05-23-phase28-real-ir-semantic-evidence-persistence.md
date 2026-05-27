# Phase 28 Real IR Source Connector + Semantic Evidence Persistence v1

## Context

Phase 27 proved the semantic extraction pipeline with mock IR and industry
materials. It can chunk documents, recall candidate passages, extract structured
claims, and apply deterministic rule gates. Phase 28 connects that pipeline to
real local source metadata and persists passed gate results as evidence graph
candidates.

## Architecture

The Phase 28 flow is:

1. Normalize real IR source metadata from local SMR tables.
2. Prefer real source inventory and explicitly report mock fallback.
3. Load parsed text or normalized snippets without writing raw files.
4. Reuse the Phase 27 chunker, retriever, mock semantic extractor, and rule gate.
5. Convert passed gate results into semantic evidence candidates.
6. Validate candidate impact on variable packs and expectation gap gates.

The first version uses existing `filing_documents`, `source_manifest`, and
`news_items` rows. It does not call raw CNINFO/IR fetch paths that persist large
raw files.

## Scope

Pilot tickers:

- `300394.SZ`
- `300308.SZ`
- `688041.SH`
- `002230.SZ`

Supported source types:

- investor relations record
- investor interaction
- earnings briefing
- annual report
- semiannual report
- quarterly report
- company announcement
- company IR webpage
- news with company quote

## Persistence Rules

- Dry-run does not write DB rows.
- Execute writes only `real_ir_sources` or `semantic_evidence_candidates`.
- Source URL is required.
- Quoted span is required.
- Source id, chunk id, and quoted span dedupe candidates.
- Mock fallback evidence is not persisted as real evidence.
- Raw source text is not written.
- `usable_for_promotion` is always false.

## Guardrails

- Do not fabricate customer names.
- Do not fabricate supplier share.
- Do not fabricate ASP.
- Do not fabricate shipment volume.
- Do not rewrite North American customer as NVIDIA.
- Do not rewrite demand strength as confirmed order.
- Do not treat management commentary as audited fact.
- Do not let semantic evidence alone create pending review.
- Do not relax promotion rules.

## Expected Result

After Phase 28, the system can answer:

- which real source URL produced a semantic claim
- which chunk and quoted span support the claim
- whether the claim passed the rule gate
- whether it became an evidence candidate
- whether it updates variable evidence packs
- why it still cannot directly trigger pending review
