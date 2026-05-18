#!/usr/bin/env python3
"""Deploy Phase 3+4: Recommendation, Portfolio, Risk, and Brief Skills + config files."""

import os

SMR_ROOT = "/Users/apple/Documents/同行资本二级市场"

files = {}

# ============================================================
# Phase 3 Skills
# ============================================================

files["09_runbooks/skills/smr-recommendation/SKILL.md"] = """---
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
- Do not recommend without confirmed trend (3+ factors).
- Do not recommend single-tranche all-in entry.
- Do not recommend with risk/reward < 2:1.
- Do not use "guaranteed", "certain", "sure" language.
- Always include disclaimer.
- All recommendations require user confirmation.

## Output guidance

Save to: `/Users/apple/Documents/同行资本二级市场/03_stock_pool/recommended/{date}/`
"""

files["09_runbooks/skills/smr-portfolio/SKILL.md"] = """---
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
"""

files["09_runbooks/skills/smr-thesis-check/SKILL.md"] = """---
name: smr-thesis-check
description: Use when checking whether the investment thesis for an open position has been invalidated. Thesis invalidation is the highest-priority exit signal, overriding all other considerations.
---

# smr-thesis-check

Use this skill for thesis invalidation detection.

## Important boundary

- This skill is the **most important risk management tool**.
- Thesis invalidation = unconditional exit recommendation.
- It does **not** consider P&L when recommending exit.
- It does **not** wait for technical confirmation.

Its job is:

> 把"投资逻辑还在不在"变成"如果不在了，立刻走人"。

## Load order

1. Read all open positions with their theses from database
2. Read latest industry/stock research from `/Users/apple/Documents/同行资本二级市场/02_research/`
3. Read latest US signals from `/Users/apple/Documents/同行资本二级市场/01_data/us_signals/`
4. Read latest risk alerts from `/Users/apple/Documents/同行资本二级市场/05_risk/`

## Core workflow

1. **For each open position**, extract the original thesis.

2. **Check thesis against current reality**:
   - Has the industry thesis changed? (e.g., policy reversal, technology route shift)
   - Has the company-specific thesis changed? (e.g., major customer loss, competitive position erosion)
   - Has the US linkage thesis changed? (e.g., US benchmark thesis broken, supply chain decoupling)
   - Has the catalyst timeline been missed without thesis playing out?

3. **Thesis status classification**:
   - **INTACT**: All core assumptions still hold, thesis on track
   - **WEAKENED**: 1-2 assumptions challenged but not disproven, monitor closely
   - **BROKEN**: Core assumption disproven, thesis no longer valid
   - **PLAYED_OUT**: Thesis has materialized as expected, take profit

4. **Action rules**:
   - INTACT → Continue holding
   - WEAKENED → Reduce position by 30-50%, set tighter stop
   - BROKEN → Exit immediately, regardless of P&L
   - PLAYED_OUT → Take profit per plan

5. **Common thesis-breaking scenarios**:
   - Embodied AI: Major customer (e.g., Tesla) shifts to in-house or alternative supplier
   - Semiconductor: Export control expansion cutting off key technology access
   - AI Agent: Major platform (e.g., Microsoft) bundles the functionality natively
   - Quantum: Government funding withdrawal or technology route obsolescence
   - CPO/Optics: Major customer (e.g., NVIDIA) changes architecture away from CPO

## Required output fields

1. **position**: ts_code and current P&L
2. **original_thesis**: The thesis as stated at entry
3. **thesis_status**: INTACT / WEAKENED / BROKEN / PLAYED_OUT
4. **evidence**: What changed and why
5. **recommended_action**: Hold / Reduce / Exit / Take Profit
6. **urgency**: Low / Medium / High / Critical

## Hard constraints

- Thesis broken = exit, no exceptions.
- Do not rationalize holding a broken thesis position.
- Do not wait for "better price" to exit a broken thesis.
- Always document why the thesis broke (learning for future).
"""

# ============================================================
# Phase 4 Skills
# ============================================================

files["09_runbooks/skills/smr-risk-alert/SKILL.md"] = """---
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
"""

files["09_runbooks/skills/smr-daily-brief/SKILL.md"] = """---
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
"""

files["09_runbooks/skills/smr-weekly-brief/SKILL.md"] = """---
name: smr-weekly-brief
description: Use when writing the weekly SMR summary. Includes weekly performance review, thesis review, sector rotation analysis, and next-week outlook.
---

# smr-weekly-brief

Use this skill for weekly summary writing.

## Core workflow

1. **Weekly performance review**:
   - Portfolio weekly return vs. benchmark
   - Best and worst performing positions
   - Win rate for the week

2. **Thesis review**:
   - For each open position: thesis status update
   - Any thesis broken this week? Lessons learned.
   - Any thesis played out this week? Profit-taking status.

3. **Sector rotation analysis**:
   - Which SMR sectors gained/lost this week?
   - Any sector rotation signals?
   - US sector performance comparison

4. **Research pipeline review**:
   - Research completed this week
   - Research in progress
   - Research backlog

5. **Next-week outlook**:
   - Key events calendar (earnings, policy, economic data)
   - Research priorities
   - Position adjustment considerations

6. **Produce weekly brief**.

## Output guidance

Save to: `/Users/apple/Documents/同行资本二级市场/06_reports/weekly/weekly_brief_{date}.md`
"""

# ============================================================
# Risk rules config
# ============================================================

files["05_risk/rules/risk_rules.md"] = """# SMR 风控规则

> 中长线趋势交易适配版

## 仓位规则

| 规则 | 阈值 | 预警级别 |
|------|------|---------|
| 单票最大仓位 | ≤25% | warning |
| 行业集中度 | ≤50% | warning |
| 总仓位上限 | ≤90%（保留10%现金） | warning |

## 回撤规则

| 规则 | 阈值 | 预警级别 |
|------|------|---------|
| 组合最大回撤 | ≤20% | critical |
| 组合回撤预警 | >15% | warning |
| 单周最大亏损 | ≤8% | critical |
| 单周亏损预警 | >5% | warning |

## 止损规则

| 规则 | 触发条件 | 动作 |
|------|---------|------|
| Thesis止损 | 投资逻辑被证伪 | 无条件退出 |
| 技术止损 | 跌破MA60 | 评估退出 |
| 技术止损（加强） | 跌破MA120 | 建议退出 |
| 固定止损 | 个股亏损>15% | 评估退出 |

## 预警升级规则

| 原始级别 | 未处理时间 | 升级后级别 |
|---------|-----------|-----------|
| warning | 24小时 | critical |
| critical | 4小时 | 重新发送+紧急标记 |

## 禁止事项

- 禁止绕过风控规则
- 禁止在critical预警未处理时开新仓
- 禁止将风控预警降级而不记录理由
- 禁止忽略thesis止损信号
"""

# ============================================================
# Deploy all files
# ============================================================

deployed = 0
for rel_path, content in files.items():
    target = os.path.join(SMR_ROOT, rel_path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content.lstrip("\n"))
    deployed += 1
    print(f"  ✅ {rel_path}")

print(f"\nDeployed {deployed} files to {SMR_ROOT}")
