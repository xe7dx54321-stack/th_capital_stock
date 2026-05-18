---
name: smr-risk-alert
description: Use when monitoring portfolio risk and generating risk alerts. Covers drawdown, position concentration, sector concentration, and thesis-based risk assessment.
---

# smr-risk-alert

Use this skill for portfolio risk monitoring and alerting.

## Important boundary

- This skill is **independent** from investment decisions.
- It does **not** consider potential returns, only risks.
- Its alerts **cannot be overridden** by other agents.
- It does **not** execute trades — only raises alerts.

Its job is:

> 把"组合的风险在哪里"变成"预警已经发出，请立即关注"。

## Load order

1. Read all open positions from database
2. Run risk engine: `python3 /Users/apple/Documents/同行资本二级市场/08_scripts/risk_engine/monitor.py`
3. Read existing alerts from `/Users/apple/Documents/同行资本二级市场/05_risk/alerts/`
4. Read risk rules from `/Users/apple/Documents/同行资本二级市场/05_risk/rules/`

## Core workflow

1. **Run automated risk checks** (via risk_engine/monitor.py):
   - Single position concentration: > 25% → warning
   - Portfolio drawdown: > 15% → warning, > 20% → critical
   - Weekly loss: > 5% → warning, > 8% → critical
   - Sector concentration: > 40% → warning, > 50% → critical

2. **Thesis-based risk check** (via smr-thesis-check skill):
   - Any position with BROKEN thesis → critical alert
   - Any position with WEAKENED thesis → warning alert

3. **Technical risk check**:
   - Any position below MA60 → warning
   - Any position below MA120 → critical
   - Any position with RSI > 80 (overbought) → info
   - Any position with RSI < 20 (oversold) → warning

4. **US linkage risk check**:
   - Major US benchmark drop > 5% in single day → warning for linked A+H stocks
   - US benchmark thesis broken → warning for linked A+H stocks

5. **Alert generation**:
   - **info**: Awareness, no action required
   - **warning**: Evaluation needed, consider action
   - **critical**: Action required, do not ignore

6. **Escalation rule**:
   - If a warning alert is not acknowledged within 24 hours → escalate to critical
   - If a critical alert is not acknowledged within 4 hours → re-alert with urgency flag

## Hard constraints

- Do not suppress or downgrade alerts without justification.
- Do not skip risk checks even when portfolio is profitable.
- Critical alerts must be addressed before any new positions are added.
- Always run risk engine before generating daily report.
