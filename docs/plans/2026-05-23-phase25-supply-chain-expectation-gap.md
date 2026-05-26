# Phase 25 Supply Chain Expectation Gap Engine v1

## Context

Phase 24 connected `cn_tender_procurement` as a partial connector. It can now
generate CN tender/procurement queries and normalize limited evidence candidates,
but the first run confirmed that full tender-platform expansion is unlikely to be
the highest-return next step for AI infrastructure, semiconductor, and optical
interconnect research.

Phase 25 therefore shifts the stack toward a supply-chain expectation gap engine.
The engine does not try to answer unavailable questions such as exact NVIDIA
orders, hyperscaler allocation, supplier share, or ASP. Instead, it makes a
scenario chain explicit:

```text
End Demand Proxy
  -> Product Demand Model
  -> Supplier Exposure Model
  -> Revenue Sensitivity Model
  -> Expectation / Consensus Proxy
  -> Expectation Gap Score
  -> Investment Gate Impact
```

## Scope

The first template is `ai_optical_interconnect`, covering AI data centers,
high-speed networking, 800G/1.6T optical modules, optical components, optical
packaging, and CPO/LPO-related supply-chain variables.

The pilot ticker set is isolated in `supply_chain_pilot`:

- `300394.SZ`
- `300308.SZ`
- `688041.SH`
- `002230.SZ`

`300394.SZ` is intentionally not added to `ai_core` in this phase.

## New Artifacts

- `00_control/supply_chain_theme_templates.json`
- `00_control/supplier_exposure_profiles.json`
- `00_control/watchlists/supply_chain_pilot.json`
- `08_scripts/lib/smr_supply_chain_theme_template.py`
- `08_scripts/lib/smr_supplier_exposure_model.py`
- `08_scripts/lib/smr_end_demand_proxy.py`
- `08_scripts/lib/smr_revenue_sensitivity_model.py`
- `08_scripts/lib/smr_expectation_gap.py`
- `08_scripts/lib/smr_phase25_utils.py`
- `08_scripts/reporting/build_phase25_end_demand_proxy.py`
- `08_scripts/reporting/build_phase25_revenue_sensitivity.py`
- `08_scripts/reporting/build_phase25_expectation_gap.py`
- `08_scripts/reporting/build_phase25_supply_chain_expectation_gap_packet.py`
- `08_scripts/reporting/build_phase25_supply_chain_gap_summary.py`
- `08_scripts/verification/validate_phase25_expectation_gap_gate_integration.py`

## Guardrails

- Supplier exposure profiles are `scenario_analysis_only`.
- Customer exposure must be `confirmed`, `proxy_only`, `not_directly_confirmed`,
  or `unknown`.
- Supplier share and ASP assumptions must be interval objects, not fabricated
  point estimates.
- Missing variables are reported instead of force-calculated.
- Industry-level proxy evidence is never treated as a company order.
- Planned sources do not count as active evidence.
- Official consensus is treated as unavailable unless a real source is added.
- Expectation gap score does not directly create pending review.
- Promotion rules are not relaxed.
- No paper order, paper position, or real trading path is introduced.

## Outputs

The Phase 25 reports provide:

- End-demand direction and confidence for `ai_optical_interconnect`.
- Scenario-only revenue sensitivity by ticker.
- Expectation gap score, confidence, uncertainty penalty, and key uncertainties.
- A per-ticker packet for research review.
- A gate integration validator that shows thesis, valuation, and bear-case impact
  without allowing gap-only promotion.
- A summary dashboard listing positive gap candidates, insufficient-data cases,
  and next connector needs.

## Validation

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/reporting/build_phase25_end_demand_proxy.py --theme ai_optical_interconnect --json
python 08_scripts/reporting/build_phase25_revenue_sensitivity.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase25_expectation_gap.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase25_supply_chain_expectation_gap_packet.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/verification/validate_phase25_expectation_gap_gate_integration.py --tickers 300394.SZ,300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase25_supply_chain_gap_summary.py --json
```

## Expected Result

Phase 25 should make the system able to answer:

- Whether AI optical interconnect end demand is positive, negative, conflicted,
  or insufficient.
- Where each supplier sits in the supply chain.
- Which variables are evidence and which are assumptions.
- Whether revenue sensitivity is calculable or scenario-only.
- Whether expectation gap is positive, neutral, negative, conflicted, or
  insufficient.
- Which connector should be added next to reduce uncertainty.
