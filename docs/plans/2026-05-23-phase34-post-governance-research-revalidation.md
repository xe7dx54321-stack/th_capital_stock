# Phase 34 Post-Governance Research Revalidation v1

## Context

Phase 33 executed a controlled evidence review sample and produced real audit
records, lifecycle updates, governance deltas, workbench incremental views, and
download repair upserts. It proved that governed review actions can execute
without relaxing promotion, creating pending review rows, creating paper orders,
or confirming sensitive variables.

Phase 34 turns those governed outcomes back into research diagnostics. It asks a
different question: after review, did the research state for each supply-chain
pilot ticker get stronger, weaker, or remain blocked by missing evidence?

The first scope remains the four supply-chain pilot tickers:

- `300394.SZ`
- `300308.SZ`
- `688041.SH`
- `002230.SZ`

## Scope

Phase 34 adds a read-only revalidation layer. It aggregates Phase 33 audit rows,
lifecycle states, semantic evidence candidates, variable-pack snapshots,
expectation-gap diagnostics, repair tasks, and conservative safety invariants.

The phase produces:

- post-governance evidence state by ticker
- variable-pack post-governance revalidation
- expectation-gap post-governance revalidation
- valuation-support post-governance revalidation
- bear-case post-governance revalidation
- ticker-level research state classification
- next evidence plan
- research revalidation packet
- post-governance research summary dashboard

## Guardrails

Phase 34 is not an investment committee, trading layer, or source-expansion
phase. It does not run more broad evidence review and does not upgrade semantic
evidence into confirmed variables.

Required invariants:

- `approved_evidence` is not promotion evidence.
- Downgraded evidence lowers or caps variable impact.
- Rejected and noisy evidence does not enter active variable-pack use.
- Supplier share is not confirmed from semantic evidence.
- ASP is not confirmed from semantic evidence.
- Customer allocation is not confirmed from semantic evidence.
- Internal proxy is not official consensus.
- Research state is not promotion status.
- `ready_for_research_packet` is not `pending_human_review`.
- No buy/sell/add/reduce recommendation is generated.
- `new_pending_created=0`.
- `paper_order_created=0`.
- `promotion_allowed_true=0`.

## Design

The implementation uses one deterministic aggregation module:

- `08_scripts/lib/smr_post_governance_evidence_state.py`

This module owns the Phase 34 evidence-state and revalidation definition. Reporting and
verification scripts call it instead of recalculating their own divergent
versions of audit/lifecycle state.

Ticker state classification lives in:

- `08_scripts/lib/smr_research_state_classifier.py`

The classifier is conservative by design. It can return:

- `research_strengthened`
- `research_weakened`
- `unchanged_needs_more_data`
- `ready_for_research_packet`
- `deprioritize`
- `blocked_by_evidence_quality`
- `unknown`

None of these states authorizes promotion or trading.

## Expected Outputs

The post-governance evidence state report answers:

- how many reviewed evidence items each ticker has
- which were approved, rejected, downgraded, marked noise, or sent for better
  source
- which variables were strengthened or weakened
- which core gaps remain
- how many repair tasks remain open

The revalidation reports answer:

- whether variable packs changed
- whether expectation gap confidence changed
- whether valuation support remains blocked
- whether bear case worsened or stayed unchanged
- what evidence is still needed next

The research revalidation packet makes the promotion boundary explicit and is
not a buy/sell report.

## Validation

Run:

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/reporting/build_phase34_post_governance_evidence_state.py --json
python 08_scripts/verification/validate_phase34_variable_pack_post_governance.py --json
python 08_scripts/verification/validate_phase34_expectation_gap_post_governance.py --json
python 08_scripts/verification/validate_phase34_valuation_support_post_governance.py --json
python 08_scripts/verification/validate_phase34_bear_case_post_governance.py --json
python 08_scripts/reporting/build_phase34_research_state_classification.py --json
python 08_scripts/reporting/build_phase34_next_evidence_plan.py --json
python 08_scripts/reporting/build_phase34_research_revalidation_packet.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase34_post_governance_research_summary.py --json
```
