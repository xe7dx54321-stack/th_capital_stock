# Phase 27 Semantic IR & Industry Forecast Evidence Extractor v1

## Context

Phase 26 made the key supply-chain expectation-gap assumptions auditable through
variable evidence packs. The next bottleneck is evidence quality: supplier
share, ASP, customer allocation, official consensus, and industry forecast
coverage still remain missing or partial.

Phase 27 adds a semantic extraction layer that can read company IR and public
industry materials as structured evidence candidates. It does not treat keyword
matches as evidence. Keywords only recall candidate chunks; semantic extraction
and deterministic gates decide whether a claim can support variable evidence.

## Architecture

The first version uses this pipeline:

1. Company IR / industry source inventory
2. Document chunker
3. Candidate retriever
4. Mock-first semantic extractor
5. Structured semantic extraction schema
6. Deterministic rule gate
7. Variable evidence pack integration
8. Expectation gap / valuation / bear case revalidation
9. Semantic evidence summary dashboard

`--mock` is the default and deterministic. `--llm` is reserved as an interface
for a later real LLM connector and is not enabled in tests or validation.

## Scope

Theme:

- `ai_optical_interconnect`

Pilot tickers:

- `300394.SZ`
- `300308.SZ`
- `688041.SH`
- `002230.SZ`

The mock source inventory models available company IR, announcements, management
discussion, news-with-company-quote, and public industry commentary. It does not
write raw HTML, PDFs, or large files.

## Guardrails

- Every extraction must have `source_id`, `chunk_id`, and `quoted_span`.
- `quoted_span` must appear in the input chunk.
- Customer names and numeric values must appear in the input chunk.
- North American customer must not be rewritten as NVIDIA.
- Strong demand must not become confirmed order.
- Product mix optimization must not become ASP increase unless explicitly stated.
- Management commentary is capped at partial/context support.
- Industry forecast can support end-demand or valuation context, not company
  orders.
- Semantic evidence alone cannot trigger pending review.
- Promotion rules remain unchanged.

## Outputs

Phase 27 adds:

- IR source inventory report
- semantic IR evidence job
- industry forecast evidence report
- semantic variable-pack integration validator
- semantic gate impact validator
- semantic evidence summary dashboard

## Expected Result

After Phase 27, the system can answer:

- which IR or industry source provided a claim
- which chunk and quoted span support the claim
- whether the claim is management commentary, direct disclosure, industry
  forecast, proxy indication, weak context, or unusable
- whether the claim can enter a variable evidence pack
- why the claim cannot directly trigger promotion or pending review
