---
name: smr-daily-brief
description: Use when writing the daily market brief for SMR. Includes US overnight analysis, A+H market overview, portfolio P&L, risk status, and next-day focus.
---

# smr-daily-brief

Use this skill for daily market brief writing.

## Important boundary

- This skill produces **informational reports**, not trading signals.
- It does **not** make investment decisions.
- It does **not** hide risks or losses.
- Every brief must include a disclaimer.

Its job is:

> 把"今天发生了什么"变成"一份信息密度高、可操作的日报"。

## Load order

1. Read US signal data from `/Users/apple/Documents/同行资本二级市场/01_data/us_signals/`
2. Read A+H market data from database
3. Read portfolio P&L from `/Users/apple/Documents/同行资本二级市场/04_portfolio/performance/`
4. Read risk alerts from `/Users/apple/Documents/同行资本二级市场/05_risk/alerts/`
5. Read research progress from `/Users/apple/Documents/同行资本二级市场/02_research/`
6. Read daily brief template from `/Users/apple/Documents/同行资本二级市场/09_runbooks/templates/daily_brief.md`

## Core workflow

1. **US overnight section**:
   - Key US benchmark moves (NVDA, TSLA, etc.)
   - Major events (earnings, guidance, analyst actions)
   - Impact assessment for A+H stocks

2. **A+H market overview**:
   - Major index performance (上证, 科创50, 恒生科技)
   - SMR sector performance (具身智能, 半导体, AI, 量子)
   - Notable stock moves in SMR universe

3. **Portfolio P&L section**:
   - Each position's daily P&L and cumulative P&L
   - Thesis status for each position
   - Total portfolio value and drawdown

4. **Risk status section**:
   - Active alerts and their status
   - Portfolio risk metrics (concentration, drawdown)
   - Any thesis status changes

5. **Research progress section**:
   - New research initiated
   - Research completed
   - Pending research triggers

6. **Next-day focus section**:
   - US events to watch (earnings, economic data)
   - A+H events to watch (IPO, policy announcements)
   - Research priorities

7. **Produce daily brief** following the template.

## Hard constraints

- Do not omit risk information.
- Do not give specific buy/sell recommendations in the brief.
- Always include disclaimer.
- Keep language concise and information-dense.
- Use data, not opinions.

## Output guidance

Save to: `/Users/apple/Documents/同行资本二级市场/06_reports/daily/daily_brief_{date}.md`
