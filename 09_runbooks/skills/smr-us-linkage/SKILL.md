---
name: smr-us-linkage
description: Use when analyzing cross-market signals from US frontier tech benchmarks and their impact on A+H stocks. Maps US earnings calls, guidance, analyst ratings, and capex trends to A+H supply chain implications.
---

# smr-us-linkage

Use this skill for US-A+H cross-market signal analysis.

## Important boundary

- This skill analyzes **signals**, not trading decisions.
- It does **not** invest in US stocks directly.
- It does **not** assume perfect correlation between US and A+H.
- It only covers US benchmarks relevant to SMR sectors.

Its job is:

> 把"美股那边发生了什么"变成"对A股和港股的哪些标的有怎样的影响"。

## Load order

1. Read `/Users/apple/Documents/同行资本二级市场/01_data/us_signals/` latest signals
2. Read `/Users/apple/Documents/同行资本二级市场/01_data/db/smr.db` — us_daily_bar and us_signal tables
3. Read `/Users/apple/Documents/同行资本二级市场/00_control/sector_priority_map.md`
4. Read factor data with us_linkage factors from `/Users/apple/Documents/同行资本二级市场/01_data/factor/`

## Core workflow

1. **Signal identification**:
   - What US event occurred? (earnings call / guidance / analyst rating / capex announcement / product launch)
   - Which US benchmark(s) are affected?
   - What was the market's reaction? (price move / volume / options activity)

2. **Transmission path mapping**:
   Four types of US-A+H linkage:
   
   | Type | Mechanism | Example |
   |------|-----------|---------|
   | Supply chain | US company orders → A+H supplier revenue | NVIDIA capex → 中际旭创 orders |
   | Technology route | US tech direction → A+H technology beneficiaries | Tesla Optimus → 绿的谐波 demand |
   | Valuation anchor | US market cap → A+H comparable valuation | IONQ market cap → 国盾量子 reference |
   | Demand sentiment | US sector sentiment → A+H sector rotation | Meta AI capex → A-share AI sentiment |

3. **Impact assessment**:
   - Direct impact: A+H stocks with direct supply chain relationship
   - Indirect impact: A+H stocks in the same sector ecosystem
   - Sentiment impact: A+H sector rotation driven by US sentiment
   - Time lag: How quickly does the signal transmit? (overnight / days / weeks)

4. **Signal strength rating**:
   - **strong**: Direct supply chain link + quantitative evidence (order numbers, revenue guidance)
   - **moderate**: Indirect ecosystem link + directional evidence
   - **weak**: Sentiment-only link, no quantitative evidence

5. **Produce US linkage analysis**.

## Required output fields

1. **signal_source**: US event description with date and source
2. **affected_us_benchmarks**: Which US stocks moved and how much
3. **transmission_paths**: Mapped paths with type classification
4. **affected_ah_stocks**: A+H stocks affected, grouped by impact type
5. **signal_strength**: strong / moderate / weak for each affected stock
6. **time_lag_estimate**: Expected transmission speed
7. **actionable_implications**: What SMR should do (trigger research / update watchlist / alert)
8. **disclaimer**: Risk warning

## Hard constraints

- Do not assume US-A+H correlation is always positive or immediate.
- Do not treat US signals as trading signals without research validation.
- Do not cover US benchmarks outside SMR sectors.
- Always include time lag uncertainty.
- Always include disclaimer.

## Output guidance

Save to: `/Users/apple/Documents/同行资本二级市场/02_research/us_linkage/{date}/`

Also update: `/Users/apple/Documents/同行资本二级市场/01_data/us_signals/{date}.md`
