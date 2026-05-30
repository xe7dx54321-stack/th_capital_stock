# Phase 80: Report Quant Consistency & Time-series Signal Integration v1

## Objective
Align Phase 79 report-extracted quantitative metrics with existing structured financial data, establish consistency checks, build time-series signals, and integrate into watchlist intelligence.

## Core Boundaries
- Report metric != automatically high confidence
- Structured metric != automatically high confidence
- Mismatch not forcibly corrected
- Revenue trend != customer share confirmation
- Gross margin trend != product mix confirmation
- R&D trend != commercial success confirmation
- No mock/fixture/raw/OCR/browser automation
- No pending/order/trade

## Tasks
1. Consistency config & rules
2. Report metric loader (from Phase 79)
3. Structured financial metric loader (from Phase 56/57)
4. Metric reconciliation (name/unit/period mapping)
5. Metric consistency checker
6. Mismatch diagnostics
7. Time-series signal builder (YoY/trend/anomaly)
8. Trend/anomaly guard (forbidden claims)
9. Claim map update
10. Evidence memory update
11. Watchlist intelligence update
12. Multi-source capability matrix update
13. Research packet
14. Internal brief
15. Brief quality lint
16. Runner
17. Dashboard
18. Tests (17 test files)
19. Runbook update

## Tickers
- 300308.SZ: baseline regression
- 688041.SH: primary target for consistency & time-series
- 300394.SZ: blocker preserved

## Acceptance
- py_compile pass
- unittest pass (all 17 Phase 80 tests)
- Phase 79 regression not regressed
- All commands runnable
- mock/fixture/raw/OCR=false
- pending/order/trade=0
