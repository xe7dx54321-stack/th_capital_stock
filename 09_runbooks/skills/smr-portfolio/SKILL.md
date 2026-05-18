---
name: smr-portfolio
description: Use when managing portfolio positions, updating P&L, and producing position adjustment recommendations. Ensures every position has a thesis, target, and stop-loss.
---

# smr-portfolio

Use this skill for portfolio position management.

## Important boundary

- This skill **manages** positions, it does not create new recommendations.
- It does **not** execute trades without user confirmation.
- It does **not** modify risk rules.
- Every position must have a thesis — positions without thesis are flagged for review.

Its job is:

> 把"我持有什么"变成"每笔持仓状态如何，是否需要调整"。

## Load order

1. Read all open positions from database `/Users/apple/Documents/同行资本二级市场/01_data/db/smr.db`
2. Read latest P&L data from `/Users/apple/Documents/同行资本二级市场/04_portfolio/performance/`
3. Read risk alerts from `/Users/apple/Documents/同行资本二级市场/05_risk/alerts/`
4. Read current recommendations from `/Users/apple/Documents/同行资本二级市场/03_stock_pool/recommended/`

## Core workflow

1. **Position review** (daily after market close):
   - Run P&L calculation: `python3 /Users/apple/Documents/同行资本二级市场/08_scripts/portfolio/pnl.py`
   - For each open position, check:
     - Is the thesis still intact?
     - Has stop-loss been triggered?
     - Has target price been reached?
     - Has the holding period expired without thesis playing out?

2. **Thesis check** for each position:
   - **Thesis intact**: Continue holding, no action needed
   - **Thesis weakened**: Flag for review, suggest reducing position
   - **Thesis broken**: Recommend immediate exit regardless of P&L
   - **Thesis played out**: Target reached, recommend taking profit

3. **Position adjustment recommendations**:
   - New entry: Only from smr-advisor's recommendation list
   - Add to position: Only if thesis strengthens and trend confirms
   - Reduce position: If thesis weakens or sector concentration too high
   - Exit position: If thesis broken, stop-loss hit, or target reached

4. **Portfolio rebalancing** (weekly):
   - Check sector concentration (must be < 50% per sector)
   - Check single position concentration (must be < 25%)
   - Check overall portfolio risk level
   - Suggest rebalancing if any rule is breached

5. **Trade recording**:
   - When user confirms a trade, record it immediately
   - Use: `python3 /Users/apple/Documents/同行资本二级市场/08_scripts/portfolio/entry.py --ts-code CODE --entry-price PRICE --shares N --thesis "THESIS"`
   - Update position file in `/Users/apple/Documents/同行资本二级市场/04_portfolio/positions/`

## Required output fields

For daily position review:
1. **position_summary**: All open positions with P&L
2. **thesis_status**: Intact / weakened / broken for each position
3. **action_items**: Specific adjustment recommendations
4. **portfolio_health**: Overall risk metrics

## Hard constraints

- Do not hold positions without a thesis.
- Do not ignore stop-loss triggers.
- Do not exceed position limits (25% single, 50% sector).
- All trades require user confirmation.
- Always run P&L update before review.

## Output guidance

Save daily review to: `/Users/apple/Documents/同行资本二级市场/04_portfolio/performance/daily_{date}.md`
