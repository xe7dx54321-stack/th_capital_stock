---
name: smr-recommendation
description: Use when producing medium/long-term stock recommendations based on research and trend analysis. Every recommendation must include thesis, catalyst timeline, entry plan, target/stop, and holding period.
---

# smr-recommendation

Use this skill for producing medium/long-term stock recommendations.

## Important boundary

- This skill produces **recommendations**, not trading orders.
- Every recommendation MUST have a thesis — no thesis, no recommendation.
- It does **not** do short-term / day-trading recommendations.
- It does **not** cover stocks outside SMR sectors.
- All recommendations require user confirmation before execution.

Its job is:

> 把"研究和趋势都指向这个方向"变成"具体怎么操作，分几步，风险在哪"。

## Load order

0. Read `/Users/apple/Documents/同行资本二级市场/09_runbooks/skills/smr-research-synthesis/SKILL.md`
1. Read relevant industry research from `/Users/apple/Documents/同行资本二级市场/02_research/industry/`
2. Read relevant stock research from `/Users/apple/Documents/同行资本二级市场/02_research/stock/`
3. Read trend analysis from `/Users/apple/Documents/同行资本二级市场/01_data/factor/`
4. Read current portfolio from `/Users/apple/Documents/同行资本二级市场/04_portfolio/positions/`
5. Read risk status from `/Users/apple/Documents/同行资本二级市场/05_risk/`
6. Read recommendation template from `/Users/apple/Documents/同行资本二级市场/09_runbooks/templates/recommendation_card.md`

## Core workflow

1. **Pre-check**:
   - Is there a completed research report for this stock? If NO → trigger smr-researcher first.
   - Is the trend judgment confirmed (3+ factors)? If NO → this stock is not ready for recommendation.
   - Is the risk status clean (no critical alerts)? If NO → address risk first.
   - Is portfolio capacity available (position < 25% per stock, sector < 50%)? If NO → explain trade-off.

2. **Thesis validation**:
   - Restate the core thesis in 2-3 sentences
   - Confirm the thesis is still intact (no thesis-breaking events since research)
   - Rate thesis strength: strong / moderate / speculative
   - Show consensus, divergence, first-party verification, and what SMR independently believes

3. **Entry plan design**:
   - Never recommend all-in at one price
   - Design 3-tranche entry: 30% initial + 40% on pullback + 30% on confirmation
   - Define pullback level (typically near MA20 or recent support)
   - Define confirmation signal (volume breakout, MA crossover, etc.)

4. **Target and stop-loss**:
   - Target price: based on valuation framework from research
   - Stop-loss price: based on thesis-breaking level (not arbitrary %)
   - Risk/reward ratio: must be > 2:1 for new positions
   - If thesis-based stop is too wide, use technical stop (MA60 break) as secondary

5. **Holding period assessment**:
   - Weekly (1-4 weeks): short-term catalyst play
   - Monthly (1-3 months): trend-following with catalyst support
   - Quarterly (3-12 months): structural thesis play
   - State the expected holding period and the reason

6. **Portfolio impact simulation**:
   - What % of portfolio will this position be after entry?
   - What is the sector concentration after entry?
   - What is the maximum drawdown if stop-loss is hit?
   - Does this pass all risk rules?

7. **Produce recommendation** following the template.

## Required output fields

1. **thesis**: Core investment logic (2-3 sentences)
2. **thesis_strength**: strong / moderate / speculative
3. **catalyst_timeline**: Near/mid/long-term catalysts with dates
4. **entry_plan**: 3-tranche entry with conditions
5. **target_price**: With valuation reasoning
6. **stop_loss**: With thesis-breaking or technical reasoning
7. **risk_reward_ratio**: Must be > 2:1
8. **holding_period**: weekly / monthly / quarterly with reasoning
9. **portfolio_impact**: Position %, sector %, max drawdown scenario
10. **disclaimer**: Mandatory risk warning

## Hard constraints

- Do not recommend without a completed research report.
- Do not recommend from a single sell-side report or a copied external conclusion.
- Do not recommend without confirmed trend (3+ factors).
- Do not recommend single-tranche all-in entry.
- Do not recommend with risk/reward < 2:1.
- Do not use "guaranteed", "certain", "sure" language.
- Always include disclaimer.
- All recommendations require user confirmation.

## Output guidance

Save to: `/Users/apple/Documents/同行资本二级市场/03_stock_pool/recommended/{date}/`
