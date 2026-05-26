# Phase 26 Supply Chain Variable Evidence Connector v1

## Context

Phase 25 introduced the supply-chain expectation gap engine. It can reason from
AI optical interconnect end demand through supplier exposure and scenario-only
revenue sensitivity into an expectation gap score. The remaining weakness is not
the scoring framework. The weakness is variable evidence.

The main missing variables are:

- supplier share
- ASP / price proxy
- capacity / shipment
- customer allocation proxy
- official consensus
- industry forecast source coverage

Phase 26 turns those missing variables into auditable evidence packs.

## Scope

The first version continues to use the `ai_optical_interconnect` theme and the
Phase 25 pilot tickers:

- `300394.SZ`
- `300308.SZ`
- `688041.SH`
- `002230.SZ`

The highest-priority names remain `300394.SZ` and `300308.SZ`, because they were
the Phase 25 potential positive gap candidates.

## Architecture

The central library is `smr_supply_chain_variable_evidence.py`. It owns:

- variable evidence schema
- confidence caps by evidence status
- source route lookup
- local evidence search
- supplier share pack
- ASP / price proxy pack
- capacity / shipment pack
- customer allocation pack
- consensus / expectation proxy pack
- industry forecast routing

Reporting scripts are thin wrappers around that library. This keeps the
guardrails consistent across all Phase 26 outputs.

## Guardrails

- `confirmed` requires direct evidence.
- `proxy_supported` requires an `evidence_id`.
- `planned_only` is never active for scoring.
- `missing` requires a missing reason.
- Supplier share assumptions are intervals only and remain scenario-only.
- ASP is never fabricated from product upgrade language.
- Capacity expansion is not treated as shipment.
- Shipment is not treated as customer allocation.
- Internal consensus proxy is not official consensus.
- Variable evidence and expectation gap never trigger pending review alone.

## Source Routing

Phase 26 extends the connector registry with source routes for:

- `supplier_share`
- `customer_allocation_proxy`
- `company_ir`
- `industry_forecast`
- `optical_module_forecast`
- `AI_capex_forecast`
- `component_price_forecast`
- `shipment_forecast`

Commercial or authorized data providers remain `planned_only` until actually
implemented.

## Outputs

The new commands produce:

- supplier share evidence packs
- ASP / price proxy packs
- capacity / shipment packs
- customer allocation proxy packs
- consensus / expectation proxy packs
- industry forecast source routing
- variable evidence expectation-gap validation
- Phase 26 variable evidence summary

## Expected Result

Phase 26 should make the system able to say:

- whether supplier share has direct evidence or only scenario assumptions
- whether ASP has direct disclosure or only context
- whether capacity evidence exists and whether shipment is still missing
- whether customer allocation is confirmed, proxy-only, or missing
- whether consensus is official or only internal proxy
- which connector should be added next

It should not create new pending review or paper trades.
