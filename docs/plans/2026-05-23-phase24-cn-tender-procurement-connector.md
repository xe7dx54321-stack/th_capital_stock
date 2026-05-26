# Phase 24: CN Tender / Procurement Connector v1

## Purpose

Phase 24 converts the Phase 23 planned `cn_tender_procurement` route into a
real, conservative connector. The connector focuses on A-share tender,
procurement, award, contract, customer project, and customer capex evidence for:

- `300308.SZ`
- `688041.SH`
- `002230.SZ`

The goal is evidence plumbing, not broad crawling. Version 1 uses local
ingested evidence, news, filing documents, and document chunks as executable
sources, then normalizes matches into evidence candidates.

## Components

- `smr_cn_tender_query_planner.py` maps ticker and company names to targeted CN
  tender/procurement queries.
- `smr_cn_tender_procurement.py` classifies and normalizes tender/procurement
  rows into standardized evidence objects.
- `smr_tender_evidence_linkage.py` converts normalized items into evidence graph
  candidates and writes them only in execute mode.
- `fetch_cn_tender_procurement.py` runs dry-run or execute mode.
- `build_phase24_cn_tender_procurement_summary.py` reports query count, result
  count, candidates, strength, and limitations.
- `validate_phase24_tender_procurement_revalidation.py` reports proxy,
  bear-case, and promotion before/after impact without changing promotion
  state.

## Evidence Rules

- Tender notices are not tender awards.
- Procurement notices are not procurement awards.
- Purchase intentions are not confirmed orders.
- Customer capex is a demand indication, not a company order.
- News mentions are context only.
- Rumors and unconfirmed claims are blocked.
- Missing `source_url` prevents evidence graph writes.
- Confirmed awards require an award/contract type plus company match and
  customer or procurer context.

## Registry Status

`cn_tender_procurement` is marked `partial` with `supporting_evidence` usage.
This reflects an executable local-search connector with limited coverage. Full
platform expansion remains planned and must not be treated as implemented.

## Safety

Phase 24 does not:

- Create pending review automatically.
- Create paper orders or positions.
- Relax promotion rules.
- Commit raw HTML, PDFs, or logs.
- Treat weak or context-only evidence as confirmed demand.

## Validation

Run:

```bash
python -m py_compile 08_scripts/lib/*.py 08_scripts/jobs/*.py 08_scripts/verification/*.py 08_scripts/reporting/*.py
python -m unittest discover -s tests -v
python 08_scripts/jobs/fetch_cn_tender_procurement.py --tickers 300308.SZ,688041.SH,002230.SZ --dry-run --json
python 08_scripts/reporting/build_phase24_cn_tender_procurement_summary.py --tickers 300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/verification/validate_phase24_tender_procurement_revalidation.py --tickers 300308.SZ,688041.SH,002230.SZ --json
python 08_scripts/reporting/build_phase24_tender_procurement_summary.py --watchlist ai_core --json
```
