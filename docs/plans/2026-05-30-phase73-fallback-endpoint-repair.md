# Phase 73: Fallback Source Endpoint Repair & Manual URL Seeding v1

## Date: 2026-05-30

## Goal
Repair fallback source endpoints (IRM HTTP 405, SSE HTTP 404, SZSE HTTP 500) and seed company IR/known URL for 688041.SH.

## Tasks
1. IRM endpoint repair (8 variants)
2. SSE endpoint repair (8 variants)
3. SZSE endpoint diagnostics (8 variants)
4. Company IR URL seeding (688041: Hygon.cn)
5. Known URL seeding (688041: Hygon IR page)
6. Seeded URL controlled fetch
7. Fallback text quality
8. Evidence rerun / gain / matrix
9. Evidence memory
10. Internal brief / quality lint
11. Runner / Dashboard
12. 16 test files

## Results
- py_compile: 0 errors
- unittest: 64/64 pass
- Phase 72: no regression
- 43 new files
