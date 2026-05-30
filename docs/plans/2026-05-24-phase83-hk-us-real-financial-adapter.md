# Phase 83: HK/US Real Financial Data Adapter v1

## Goal
Connect HK and US real structured financial data sources to the Phase 82 multi-ticker monitoring framework.

## Target Tickers
- 09988.HK (Alibaba)
- 00700.HK (Tencent)
- NVDA (NVIDIA)
- AVGO (Broadcom)

## Key Decisions
1. HK adapter uses akshare_hk_financial + yfinance_financials fallback
2. US adapter uses yfinance_financials + SEC companyfacts fallback
3. HKD/USD/CNY never directly compared across markets
4. FY/Q/TTM/YTD period policies handled separately per market
5. Statement schema mapping bridges HK/US field names to standard metrics
6. Derived metrics (gross_margin, R&D_expense_ratio) computed from loaded values
7. Unavailable tickers get specific, ticker-level, source-level blockers

## Integration Points
- Phase 82 multi-ticker quant monitoring board expanded from 3 to 7 covered tickers
- Watchlist intelligence updated with HK/US financial monitoring decisions
- Multi-source capability matrix distinguishes CN_A/HK/US coverage
- Evidence memory written with HK/US source traces

## Boundaries
- No mock/fixture for financial data
- No raw PDF/HTML saved
- No OCR or browser automation
- No pending/order/trade generated
- 300394.SZ blocker preserved
- A-share coverage not regressed
