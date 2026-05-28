# Phase 35 Single-Stock Research Packet v1

## Context

Phase 34 revalidated supply-chain pilot tickers after evidence governance. It
showed that `300394.SZ`, `300308.SZ`, and `688041.SH` still need more data, while
`002230.SZ` was weakened by the governed evidence review.

Phase 35 narrows the work to the first two single-stock research packets:

- `300394.SZ`
- `300308.SZ`

Both remain `unchanged_needs_more_data`. The research line is still worth
organizing, but the evidence is not strong enough for pending review.

## Scope

Phase 35 adds a deterministic research-packet layer over existing Phase 34
outputs. It synthesizes:

- research thesis
- evidence chain
- variable coverage matrix
- expectation gap
- valuation support
- bear case
- research quality
- bull/base/bear research scenarios
- why-not-pending explainer
- next evidence plan
- two-ticker dashboard

## Guardrails

Phase 35 is not a trading, promotion, or paper-order phase.

Required invariants:

- No buy/sell/add/reduce recommendation.
- No target price.
- No position guidance.
- No new `pending_human_review`.
- No approved paper.
- No paper order or paper position.
- Semantic evidence does not confirm supplier share.
- Semantic evidence does not confirm ASP.
- Semantic evidence does not confirm customer allocation.
- Internal proxy is not official consensus.
- `promotion_allowed=false`.
- `new_pending_created=0`.
- `paper_order_created=0`.
- No raw PDF, HTML, cache, DB, log, or generated HTML artifacts are committed.

## Implementation

New library modules:

- `08_scripts/lib/smr_single_stock_thesis_builder.py`
- `08_scripts/lib/smr_research_evidence_chain.py`
- `08_scripts/lib/smr_research_quality_scoring.py`

New reporting scripts:

- `08_scripts/reporting/build_phase35_single_stock_thesis.py`
- `08_scripts/reporting/build_phase35_evidence_chain_packet.py`
- `08_scripts/reporting/build_phase35_variable_coverage_matrix.py`
- `08_scripts/reporting/build_phase35_research_quality_score.py`
- `08_scripts/reporting/build_phase35_research_scenarios.py`
- `08_scripts/reporting/build_phase35_why_not_pending.py`
- `08_scripts/reporting/build_phase35_single_stock_research_packet.py`
- `08_scripts/reporting/build_phase35_research_packet_dashboard.py`

## Expected Behavior

The thesis builder says the company may benefit from the AI optical
interconnect theme, but it does not say the benefit is confirmed.

The evidence chain keeps source URL, source type, lifecycle status, allowed
usage, and quoted span. Rejected and noisy evidence is excluded from key
evidence.

The variable matrix keeps missing variables visible, especially supplier share,
ASP, customer allocation, and official consensus.

The research quality score can be `low` or `medium_low`, but not `high`.
Research readiness remains `needs_more_data`.

The full packet is a research work packet, not an investment memo. Promotion,
pending, and paper-order boundaries remain explicit and false.

## Validation

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/verification/validate_phase3_e2e.py
python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA --days 180 --timeout 240
python 08_scripts/verification/validate_phase5_paper_portfolio_smoke.py
python 08_scripts/verification/validate_phase6_multi_ticker_live.py --watchlist ai_core --save-run-history --compare-last-run --timeout 240
python 08_scripts/verification/validate_phase14_thesis_aware_multi_ticker_live.py --watchlist ai_core --timeout 240 --json
python 08_scripts/reporting/build_phase34_post_governance_research_summary.py --json
python 08_scripts/reporting/build_phase35_single_stock_thesis.py --ticker 300394.SZ --json
python 08_scripts/reporting/build_phase35_evidence_chain_packet.py --ticker 300394.SZ --json
python 08_scripts/reporting/build_phase35_variable_coverage_matrix.py --ticker 300394.SZ --json
python 08_scripts/reporting/build_phase35_research_quality_score.py --ticker 300394.SZ --json
python 08_scripts/reporting/build_phase35_research_scenarios.py --ticker 300394.SZ --json
python 08_scripts/reporting/build_phase35_why_not_pending.py --ticker 300394.SZ --json
python 08_scripts/reporting/build_phase35_single_stock_research_packet.py --ticker 300394.SZ --json
python 08_scripts/reporting/build_phase35_single_stock_research_packet.py --ticker 300308.SZ --json
python 08_scripts/reporting/build_phase35_research_packet_dashboard.py --json
```
