# Phase 23: Source Connector Registry v2 + Valuation Source Routing

## Context

Phase 22 made valuation, demand, and proxy blockers more precise. The remaining
problem is operational: when the system says a blocker is missing evidence, it
also needs to know where that evidence should come from, which connector can
provide it, and whether that connector is implemented, partial, planned, or
unavailable.

Phase 23 adds that routing layer without changing promotion rules or fetching
new external data.

## Goals

1. Define `source_connector_registry_v2.json`.
2. Define `blocker_source_route_map.json`.
3. Map valuation blockers to information types and source routes.
4. Map demand, order, tender, customer-capex, and proxy blockers to source
   routes.
5. Generate source acquisition plans from Phase 22 repair tasks.
6. Build a connector availability dashboard.
7. Validate that major blockers have routes and acquisition plans.

## Non-goals

- No new industry-chain agent.
- No new investment committee agent.
- No real trading.
- No watchlist expansion.
- No large raw files.
- No promotion-rule relaxation.
- No treating planned connectors as implemented.
- No treating internal proxy or proxy EPS as official consensus.
- No paper orders or paper positions.

## Design

The core route is:

```text
blocker
  -> information_type
  -> source route
  -> connector
  -> fallback
  -> source acquisition plan
```

The registry stores connector status and allowed usage. Planned connectors are
visible for roadmap purposes, but cannot be used as evidence. Context-only
sources can inform diagnostics but cannot support promotion.

## New Files

- `00_control/source_connector_registry_v2.json`
- `00_control/blocker_source_route_map.json`
- `08_scripts/lib/smr_source_connector_registry.py`
- `08_scripts/lib/smr_blocker_source_router.py`
- `08_scripts/lib/smr_source_acquisition_plan.py`
- `08_scripts/reporting/build_phase23_source_connector_registry_report.py`
- `08_scripts/reporting/build_phase23_valuation_source_routing.py`
- `08_scripts/reporting/build_phase23_demand_source_routing.py`
- `08_scripts/reporting/build_phase23_source_acquisition_plan.py`
- `08_scripts/reporting/build_phase23_connector_availability_dashboard.py`
- `08_scripts/verification/validate_phase23_source_routing_revalidation.py`

## Safety Rules

- `official_consensus` must remain `planned_only` until a real connector exists.
- Internal proxy can be a fallback, but it is not official consensus.
- Tender/procurement connectors are planned unless explicitly implemented.
- Planned connectors do not write evidence graph entries.
- Source routing does not create pending review or paper orders.

## Validation

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/reporting/build_phase23_source_connector_registry_report.py --json
python 08_scripts/reporting/build_phase23_valuation_source_routing.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase23_demand_source_routing.py --watchlist ai_core --json
python 08_scripts/reporting/build_phase23_source_acquisition_plan.py --tickers 300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase23_connector_availability_dashboard.py --json
python 08_scripts/verification/validate_phase23_source_routing_revalidation.py --watchlist ai_core --json
```

## Expected Outcome

Phase 23 should make the system able to answer where to look next for forward
EPS, confirmed orders, tender/procurement evidence, customer capex, peer
valuation, historical valuation, and proxy independent sources. It should not
change promotion state by itself.
