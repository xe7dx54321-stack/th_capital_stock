---
name: smr-trend-analysis
description: Use when analyzing medium/long-term trend signals for SMR universe stocks based on factor data. Produces trend judgments (not trading signals) for weekly-to-quarterly holding periods.
---

# smr-trend-analysis

Use this skill for medium/long-term trend analysis of SMR universe stocks.

## Important boundary

- This skill produces **trend judgments**, not trading signals.
- It only covers **medium/long-term** trends (weekly to quarterly).
- It does **not** do intraday or short-term analysis.
- It does **not** use high-frequency factors.

Its job is:

> 把"因子数据告诉我什么"变成"中长线趋势方向是什么，强度如何"。

## Load order

1. Read factor data from `/Users/apple/Documents/同行资本二级市场/01_data/factor/`
2. Read latest daily bars from database `/Users/apple/Documents/同行资本二级市场/01_data/db/smr.db`
3. Read US linkage factors
4. Read existing trend analysis from `/Users/apple/Documents/同行资本二级市场/02_research/`

## Core workflow

1. **Factor review**:
   Review the following factor categories:
   
   | Category | Factors | Timeframe |
   |----------|---------|-----------|
   | Trend | MA20/60/120, MACD(weekly), trend_strength | Weekly+ |
   | Fundamental | PE_TTM, PB, ROE, revenue growth | Quarterly |
   | Capital flow | Northbound net inflow (5d/20d), margin balance change | Weekly |
   | US linkage | US benchmark momentum transmission | Weekly |
   | Volatility | 20d/60d annualized volatility | Risk assessment |

2. **Multi-factor convergence check**:
   A trend is confirmed when **3+ factor categories align**:
   - Trend factors: price above MA60, MA20 > MA60, MACD bullish
   - Fundamental factors: revenue growth accelerating, ROE expanding
   - Capital flow: northbound inflow increasing, margin balance rising
   - US linkage: US benchmark momentum positive
   - Volatility: not extreme (avoid parabolic moves)

3. **Trend direction judgment**:
   - **uptrend**: 3+ categories bullish, thesis intact
   - **downtrend**: 3+ categories bearish, thesis may be broken
   - **sideways/unclear**: mixed signals, no strong direction
   - **trend reversal**: previously strong trend showing 2+ categories reversing

4. **Trend strength scoring** (0-10):
   - 8-10: Strong confirmed trend, multiple factors aligned
   - 5-7: Moderate trend, some factors aligned
   - 3-4: Weak trend, conflicting signals
   - 0-2: No trend, random walk

5. **Key level identification**:
   - Support levels: MA60, MA120, recent swing lows
   - Resistance levels: MA20 (in downtrend), recent swing highs
   - Trend break levels: where trend judgment would change

6. **Produce trend analysis report**.

## Required output fields

1. **trend_direction**: uptrend / downtrend / sideways / reversal
2. **trend_strength**: 0-10 score
3. **converging_factors**: Which factor categories support the trend
4. **diverging_factors**: Which factor categories contradict
5. **key_levels**: Support and resistance levels
6. **trend_break_trigger**: What would change the trend judgment
7. **holding_period_assessment**: Whether current trend supports weekly / monthly / quarterly holding
8. **disclaimer**: Risk warning

## Hard constraints

- Do not produce short-term (daily/intraday) trend analysis.
- Do not use high-frequency factors (tick-level, minute-level).
- Do not give specific entry/exit prices.
- A trend judgment requires 3+ factor categories — no single-factor calls.
- Always include what would break the trend.
- Always include disclaimer.

## Output guidance

Update factor data first by running:
```bash
python3 /Users/apple/Documents/同行资本二级市场/08_scripts/factor_engine/trend.py
python3 /Users/apple/Documents/同行资本二级市场/08_scripts/factor_engine/us_linkage.py
```

Save analysis to: `/Users/apple/Documents/同行资本二级市场/01_data/factor/trend_analysis_{date}.md`
