---
name: smr-stock-research
description: Use when conducting deep research on individual A+H stocks within SMR-covered sectors. Produces stock research reports with thesis, valuation framework, and entry/exit logic for medium/long-term positions.
---

# smr-stock-research

Use this skill for individual stock deep research within SMR sectors.

## Important boundary

- This skill produces **stock research**, not trading orders.
- It does **not** decide position sizing.
- It does **not** set exact entry prices (that is smr-advisor's job).
- It only covers A+H stocks in SMR sectors.

Its job is:

> 把"这家公司是做什么的"变成"这家公司在中长线趋势中的定位是什么，值不值得跟踪"。

## Load order

0. Read `/Users/apple/Documents/同行资本二级市场/09_runbooks/skills/smr-research-synthesis/SKILL.md`
1. Read `/Users/apple/Documents/同行资本二级市场/00_control/sector_priority_map.md`
2. Read relevant industry research from `/Users/apple/Documents/同行资本二级市场/02_research/industry/`
3. Read VCR project card for this company (if exists, read-only): `/Users/apple/Documents/虚拟vc项目开发规划/同行资本运行台/04_project_cards/`
4. Read factor data for this stock from `/Users/apple/Documents/同行资本二级市场/01_data/factor/`
5. Read current position status (if any) from `/Users/apple/Documents/同行资本二级市场/04_portfolio/positions/`

## Core workflow

1. **Company profiling**:
   - Business model and revenue structure
   - Position in the supply chain (upstream/midstream/downstream)
   - Key customers and their concentration risk
   - Technology differentiation vs. competitors

2. **Fundamental analysis**:
   - Revenue growth trajectory (quarterly YoY)
   - Profitability trend (gross margin, net margin, ROE)
   - Balance sheet health (debt ratio, cash position)
   - Capital expenditure plans and their strategic implications

3. **Thesis formation for this stock**:
   - How does this stock benefit from the sector thesis?
   - What is this stock's unique edge within the sector?
   - Is the thesis based on order visibility, technology moat, or policy tailwind?
   - What is the expected holding period for this thesis to play out?

4. **Valuation framework**:
   - Current PE_TTM / PB / PS vs. historical range
   - Comparable company valuation in A+H and US markets
   - Whether current valuation reflects the thesis or has room to expand
   - Key valuation drivers and their sensitivity

5. **US linkage for this stock**:
   - Which US benchmark's performance most correlates with this stock?
   - Recent US benchmark signals and their expected impact
   - Supply chain mapping: does this stock directly supply / compete with US benchmarks?

6. **Risk assessment**:
   - Customer concentration risk
   - Technology obsolescence risk
   - Valuation overextension risk
   - Thesis-breaking scenarios specific to this stock

7. **Produce stock research report** following the template.

8. **Synthesis gate**:
   - Do not treat a single external report as the conclusion.
   - Compare at least 3 reports from at least 2 institutions when available.
   - Separate consensus, divergence, first-party verification, and SMR's own judgment.
   - If evidence is incomplete, label the report as `素材型假设` or `中等置信假设`.

## Required output fields

Every stock research report must include:

1. **thesis**: Stock-specific investment logic
2. **sector_thesis_link**: How this connects to the broader sector thesis
3. **competitive_position**: Leader / challenger / niche / commodity
4. **valuation_assessment**: Undervalued / fair / overvalued / speculative
5. **us_linkage**: Relevant US benchmark and transmission mechanism
6. **key_risks**: Top 3 stock-specific risks
7. **thesis_breakers**: What would prove this stock thesis wrong
8. **suggested_pool**: watchlist / candidate / recommended / drop (with reasoning)
9. **disclaimer**: Risk warning

## Hard constraints

- Do not research stocks outside SMR sectors.
- Do not give specific buy/sell price targets (that is smr-advisor's job).
- Do not recommend short-term trading.
- Do not copy sell-side conclusions into SMR conclusions.
- Always include disclaimer.
- Always cite data sources.

## Output guidance

Save to: `/Users/apple/Documents/同行资本二级市场/02_research/stock/{ts_code}/{report-id}/`

Required files:
- `00_research-card.md`
- `thesis.md`
- `valuation.md`
- `us_linkage.md`
- `risk_assessment.md`
- `conclusion.md`
