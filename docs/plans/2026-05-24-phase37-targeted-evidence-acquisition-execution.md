# Phase 37 Targeted Evidence Acquisition Execution v1

## Context

Phase 36 produced a targeted evidence acquisition plan. It identified
`300308.SZ` as the first ticker suitable for controlled acquisition execution
because it already had partial semantic evidence coverage, and it identified
`300394.SZ` as a repair case because the current evidence chain was empty.

Phase 37 executes a small slice of that plan. The phase is about controlled
source scan, deterministic semantic extraction, guarded candidate generation,
and conservative research revalidation. It is not a pending-review or trading
phase.

## Scope

Phase 37 covers:

- controlled acquisition task selection
- targeted source scan
- targeted semantic extraction
- targeted evidence candidate building
- `300308.SZ` post-acquisition revalidation
- `300308.SZ` refreshed research packet
- `300394.SZ` evidence-chain repair dry-run
- execution dashboard

## Guardrails

Required invariants:

- No watchlist expansion.
- No complex new agent.
- No large external crawl.
- No raw PDF, raw HTML, text cache, DB, log, or generated HTML commit.
- No OCR by default.
- No fabricated supplier share.
- No fabricated ASP.
- No fabricated customer allocation.
- No internal proxy represented as official consensus.
- No industry forecast represented as company-specific confirmed order.
- No management commentary represented as confirmed order.
- No new `pending_human_review`.
- No approved paper.
- No paper order or paper position.
- No real trading path.
- `usable_for_promotion=false` for Phase 37 generated candidates.

## Implementation

New library modules:

- `08_scripts/lib/smr_controlled_acquisition_selector.py`
- `08_scripts/lib/smr_targeted_source_scan.py`
- `08_scripts/lib/smr_targeted_semantic_extraction.py`
- `08_scripts/lib/smr_targeted_evidence_candidate_builder.py`

New jobs, reporting scripts, and validators:

- `08_scripts/reporting/build_phase37_controlled_acquisition_selection.py`
- `08_scripts/jobs/run_phase37_targeted_source_scan.py`
- `08_scripts/jobs/run_phase37_targeted_semantic_extraction.py`
- `08_scripts/jobs/build_phase37_targeted_evidence_candidates.py`
- `08_scripts/verification/validate_phase37_300308_post_acquisition_revalidation.py`
- `08_scripts/reporting/build_phase37_300308_refreshed_research_packet.py`
- `08_scripts/jobs/run_phase37_300394_evidence_chain_repair.py`
- `08_scripts/verification/validate_phase37_300394_evidence_chain_repair.py`
- `08_scripts/reporting/build_phase37_execution_dashboard.py`

New tests:

- `tests/test_phase37_controlled_acquisition_selection.py`
- `tests/test_phase37_targeted_source_scan.py`
- `tests/test_phase37_targeted_semantic_extraction.py`
- `tests/test_phase37_targeted_evidence_candidate_builder.py`
- `tests/test_phase37_300308_post_acquisition_revalidation.py`
- `tests/test_phase37_300308_refreshed_packet.py`
- `tests/test_phase37_300394_evidence_chain_repair.py`
- `tests/test_phase37_execution_dashboard.py`

## Expected Behavior

The controlled selector chooses 3-5 tasks and keeps supplier-share confirmation
out of the executable path. Official consensus tasks are source-availability
only.

The source scan searches existing local state and text cache. It does not
download large documents and does not turn metadata or titles into body text.

The semantic extractor validates that every quoted span comes from the scanned
chunk. It keeps product mix, ASP proxy, order visibility, customer allocation
proxy, and industry forecast separate.

The candidate builder uses the existing quality/noise persistence guard and
keeps `usable_for_promotion=false`. Dry-run does not write DB rows.

The `300308.SZ` revalidation can report `modestly_strengthened`, but supplier
share, official consensus, and confirmed customer allocation remain missing.

The `300394.SZ` repair job is successful if it identifies root cause and repair
next steps without fabricating evidence.

## Validation

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase36_evidence_acquisition_dashboard.py --json
python 08_scripts/reporting/build_phase37_controlled_acquisition_selection.py --ticker 300308.SZ --json
python 08_scripts/jobs/run_phase37_targeted_source_scan.py --ticker 300308.SZ --dry-run --json
python 08_scripts/jobs/run_phase37_targeted_semantic_extraction.py --ticker 300308.SZ --dry-run --json
python 08_scripts/jobs/build_phase37_targeted_evidence_candidates.py --ticker 300308.SZ --dry-run --json
python 08_scripts/verification/validate_phase37_300308_post_acquisition_revalidation.py --json
python 08_scripts/reporting/build_phase37_300308_refreshed_research_packet.py --json
python 08_scripts/jobs/run_phase37_300394_evidence_chain_repair.py --dry-run --json
python 08_scripts/verification/validate_phase37_300394_evidence_chain_repair.py --json
python 08_scripts/reporting/build_phase37_execution_dashboard.py --json
```
