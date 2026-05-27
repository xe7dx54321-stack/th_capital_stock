# Phase 30 Semantic Evidence Quality & Persistence Hardening

## Goal

Phase 30 hardens Phase 29 semantic evidence candidates before persistence. The
focus is quality scoring, noise filtering, execute-safe persistence, and
post-write audit. This phase does not expand extraction scope or relax promotion
rules.

## Starting Point

- Phase 29 produced real text extraction and semantic candidates.
- Current checkpoint: `1fd7ac1b629abf2e964b920bf173034a87a11013`.
- `text_extracted=12`
- `semantic_extractions=88`
- `evidence_candidates_created=66`
- `evidence_candidates_written=0`

## Implementation

1. Score every semantic evidence candidate across quoted span, source quality,
   section quality, variable relevance, specificity, quantification, freshness,
   noise risk, duplication risk, and promotion safety.
2. Detect table fragments, PPT title-only spans, metadata-only snippets,
   headers, footers, disclaimers, legal boilerplate, and numeric-only fragments.
3. Require execute mode to pass quality, noise, dedupe, and promotion-safety
   guards before writing evidence candidates.
4. Add candidate review and hardening summaries for human audit.
5. Add post-persistence audit for variable pack and gate impact.
6. Add repair plan output for download-unavailable sources.
7. Keep connector registry conservative: all new Phase 30 connectors are
   `partial`, not `implemented`.

## Guardrails

- No raw PDF, raw HTML, text cache, DB, or log files are committed.
- OCR is not enabled by default.
- Review-required candidates are not written by default.
- `usable_for_promotion` remains false.
- Semantic evidence alone cannot create pending review.
- No confirmed supplier share, ASP, customer allocation, or official consensus
  is fabricated.
- No paper order, paper position, or real trade is created.

## Validation

Run the Phase 30 validation block from the runbook, including py_compile,
unittest, Phase 3/4/5/6/14 regressions, Phase 29 summary, Phase 30 quality
report, candidate review, persistence guard, post-persistence audit, repair
plan, hardening summary, and connector dashboard.
