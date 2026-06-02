def build_expansion_brief_md():
 return """# Phase121 External Data Source Expansion Report

## Key Finding
HK/US tickers currently rely on 1-2 data sources. Phase121 defines 11 new external source candidates across official filings, market quotes, news/events, and transcripts/guidance.

## Source Registry
- 11 total source candidates (5 official + 6 third-party)
- 6 official filing types: HKEX annual/interim, SEC 10-K/10-Q/8-K, CNINFO annual
- 5 news aggregation sources: HKEX announcements, SEC press, Finviz, Google Finance, AAStocks
- 3 market quote sources: Yahoo Finance, Akshare, Alpha Vantage (free tier)
- 4 transcript/guidance sources: Motley Fool, Seeking Alpha, HKEX results, Company IR

## HK/US Adapter Status
- 09988.HK: 2 existing -> 6 candidate sources
- 00700.HK: 2 existing -> 6 candidate sources
- NVDA: 1 existing -> 8 candidate sources
- AVGO: 1 existing -> 8 candidate sources

## Single-Source Risk Reduction
- NVDA: critical -> moderate (after network probe)
- AVGO: critical -> moderate (after network probe)
- 09988/00700: high -> reduced (after network probe)

## Known Limitations
- 12 sources need network probe verification
- 300394 CNINFO blocker unchanged (critical/manual)
- 688041 valuation gap unchanged (high/owner)
- Transcript sources remain partially manual
- No investment recommendations generated
- No trading signals produced
- Research-only, all safety boundaries enforced"""
