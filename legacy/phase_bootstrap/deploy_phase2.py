#!/usr/bin/env python3
"""Deploy Phase 2: SMR Skills, templates, and control center files."""

import os

SMR_ROOT = "/Users/apple/Documents/同行资本二级市场"

files = {}

# ============================================================
# Skills
# ============================================================

files["09_runbooks/skills/smr-industry-research/SKILL.md"] = """---
name: smr-industry-research
description: Use when conducting deep industry research on frontier tech sectors (embodied AI, semiconductor, AI agent, quantum) for medium/long-term trend trading. Produces research reports with thesis, catalyst timeline, and risk assessment.
---

# smr-industry-research

Use this skill for deep industry research on SMR-covered sectors:

- embodied AI / robotics
- semiconductor (compute + photonics)
- AI agent / application
- quantum / frontier science

## Important boundary

- This skill produces **research**, not trading signals.
- It does **not** decide entry/exit prices.
- It does **not** replace human investment judgment.
- It does **not** cover traditional industries (energy, consumer, metals, etc.).

Its job is:

> 把"这个行业发生了什么"变成"这个行业的中长线趋势方向是什么，为什么"。

## Load order

1. Read `/Users/apple/Documents/同行资本二级市场/00_control/sector_priority_map.md`
2. Read the relevant sector strategy from `/Users/apple/Documents/虚拟vc项目开发规划/同行资本运行台/00_control_tower/subsector_strategy_cards/` (read-only, VCR cognitive reuse)
3. Read `/Users/apple/Documents/同行资本二级市场/01_data/factor/` latest factor data if available
4. Read `/Users/apple/Documents/同行资本二级市场/01_data/us_signals/` latest US signals if available
5. Read `/Users/apple/Documents/同行资本二级市场/02_research/` for existing research on the same sector

## Core workflow

1. **Identify the trigger**: What triggered this research?
   - VCR project card change (new company / thesis shift)
   - US benchmark major event (earnings / guidance / analyst rating)
   - A+H price breakout of key trend lines
   - User-specified topic

2. **Industry landscape scan**:
   - Current industry lifecycle stage (early / growth / mature / declining)
   - Key technology routes and their competitive dynamics
   - Supply chain structure (upstream → midstream → downstream)
   - Policy environment and regulatory trends
   - Capital expenditure trends from major players

3. **Thesis formation**:
   - What is the core investment logic for this sector?
   - What structural trend is driving value creation?
   - Is this a supply-constrained or demand-driven opportunity?
   - What is the competitive moat structure?

4. **Catalyst identification**:
   - Near-term catalysts (1-4 weeks): earnings, product launches, policy events
   - Mid-term catalysts (1-3 months): technology milestones, order visibility
   - Long-term catalysts (3-12 months): industry inflection points, regulatory changes
   - For each catalyst: probability assessment and potential impact magnitude

5. **US linkage analysis** (if applicable):
   - Which US benchmarks are relevant?
   - What is the signal transmission path? (supply chain / technology route / valuation anchor / demand sentiment)
   - Recent US benchmark events and their implications for A+H

6. **Risk assessment**:
   - Technology risk (route competition, obsolescence)
   - Policy risk (export controls, subsidies withdrawal)
   - Valuation risk (overheated sector rotation)
   - Liquidity risk (small-cap concentration)
   - Thesis-breaking scenarios: what would prove this thesis wrong?

7. **Produce research report** following the template.

## Required output fields

Every industry research report must include:

1. **thesis**: The core investment logic (2-3 sentences max)
2. **thesis_strength**: strong / moderate / speculative
3. **catalyst_timeline**: Near-term / mid-term / long-term catalysts with dates
4. **sector_lifecycle**: early / growth / mature / declining
5. **supply_chain_map**: Key upstream → midstream → downstream players
6. **us_linkage**: Relevant US benchmarks and transmission paths
7. **risk_assessment**: Top 3 risks with probability and impact
8. **thesis_breakers**: What would prove this thesis wrong
9. **watchlist_additions**: Suggested stocks to add to watchlist
10. **disclaimer**: Risk warning and disclaimer

## Hard constraints

- Do not produce research without a clear thesis.
- Do not cover traditional industries.
- Do not give specific entry/exit price recommendations.
- Do not use "guaranteed" or "certain" language.
- Always include disclaimer.
- Always cite data sources.
- Always include thesis-breaking scenarios.

## Output guidance

Save research report to:
`/Users/apple/Documents/同行资本二级市场/02_research/industry/{sector}/{report-id}/`

Required files:
- `00_research-card.md` — metadata card
- `thesis.md` — core investment logic
- `catalyst.md` — catalyst timeline
- `risk_assessment.md` — risk analysis
- `us_linkage.md` — US linkage analysis (if applicable)
- `conclusion.md` — summary and watchlist suggestions
"""

files["09_runbooks/skills/smr-stock-research/SKILL.md"] = """---
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

## Required output fields

Every stock research report must include:

1. **thesis**: Stock-specific investment logic
2. **sector_thesis_link**: How this connects to the broader sector thesis
3. **competitive_position**: Leader / challenger / niche / commodity
4. **valuation_assessment**: Undervalued / fair / overvalued / speculative
5. **us_linkage**: Relevant US benchmark and transmission mechanism
6. **key_risks**: Top 3 stock-specific risks
7. **thesis_breakers**: What would prove this stock thesis wrong
8. **suggested_pool**: watchlist / candidate / recommended (with reasoning)
9. **disclaimer**: Risk warning

## Hard constraints

- Do not research stocks outside SMR sectors.
- Do not give specific buy/sell price targets (that is smr-advisor's job).
- Do not recommend short-term trading.
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
"""

files["09_runbooks/skills/smr-us-linkage/SKILL.md"] = """---
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
"""

files["09_runbooks/skills/smr-trend-analysis/SKILL.md"] = """---
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
"""

# ============================================================
# Templates
# ============================================================

files["09_runbooks/templates/industry_research_card.md"] = """---
report_id: {report_id}
report_type: industry
sector: {sector}
title: {title}
created_at: {date}
status: draft
---

# {title}

## Thesis

{thesis}

## Thesis Strength: {thesis_strength}

## Sector Lifecycle: {sector_lifecycle}

## Catalyst Timeline

### Near-term (1-4 weeks)
- 

### Mid-term (1-3 months)
- 

### Long-term (3-12 months)
- 

## Supply Chain Map

| Layer | Key Players | Role |
|-------|------------|------|
| Upstream | | |
| Midstream | | |
| Downstream | | |

## US Linkage

| US Benchmark | Transmission Type | A+H Impact |
|-------------|-------------------|------------|
| | | |

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| | | | |

## Thesis Breakers

1. 
2. 
3. 

## Watchlist Additions

| Stock | Code | Reason |
|-------|------|--------|
| | | |

---

⚠️ 风险提示与免责声明

本内容仅供研究参考，不构成任何投资建议。股市有风险，投资需谨慎。
过往业绩不代表未来表现。请根据自身风险承受能力独立做出投资决策。
中长线趋势判断存在不确定性，市场可能长期偏离基本面逻辑。
作者及同行资本不对因参考本内容造成的任何投资损失承担责任。
"""

files["09_runbooks/templates/stock_research_card.md"] = """---
report_id: {report_id}
report_type: stock
sector: {sector}
ts_code: {ts_code}
title: {title}
created_at: {date}
status: draft
---

# {title}

## Thesis

{thesis}

## Sector Thesis Link

{sector_thesis_link}

## Competitive Position: {competitive_position}

## Valuation Assessment: {valuation_assessment}

## Key Financials

| Metric | Latest | Trend |
|--------|--------|-------|
| Revenue YoY | | |
| Gross Margin | | |
| Net Margin | | |
| ROE | | |
| PE_TTM | | |
| PB | | |

## US Linkage

| US Benchmark | Link Type | Impact |
|-------------|-----------|--------|
| | | |

## Key Risks

1. 
2. 
3. 

## Thesis Breakers

1. 
2. 
3. 

## Suggested Pool: {suggested_pool}

Reasoning: 

---

⚠️ 风险提示与免责声明

本内容仅供研究参考，不构成任何投资建议。股市有风险，投资需谨慎。
过往业绩不代表未来表现。请根据自身风险承受能力独立做出投资决策。
中长线趋势判断存在不确定性，市场可能长期偏离基本面逻辑。
作者及同行资本不对因参考本内容造成的任何投资损失承担责任。
"""

files["09_runbooks/templates/recommendation_card.md"] = """---
report_id: {report_id}
report_type: recommendation
sector: {sector}
ts_code: {ts_code}
title: {title}
created_at: {date}
status: draft
holding_period: {holding_period}
---

# {title}

## Thesis

{thesis}

## Catalyst Timeline

| Date | Event | Expected Impact |
|------|-------|----------------|
| | | |

## Entry Plan

| Tranche | % of Target | Condition |
|---------|-------------|-----------|
| 1st | 30% | Current level |
| 2nd | 40% | On pullback to support |
| 3rd | 30% | On trend confirmation |

## Target & Stop

| | Price | Reasoning |
|--|-------|-----------|
| Target | | |
| Stop Loss | | |
| Risk/Reward | | |

## Holding Period: {holding_period}

Reasoning: 

## Current Portfolio Impact

- Position after entry: % of portfolio
- Sector concentration after entry: %
- Risk check: PASS / FAIL

## Disclaimer

⚠️ 风险提示与免责声明

本内容仅供研究参考，不构成任何投资建议。股市有风险，投资需谨慎。
过往业绩不代表未来表现。请根据自身风险承受能力独立做出投资决策。
中长线趋势判断存在不确定性，市场可能长期偏离基本面逻辑。
本推荐基于深度研究和趋势判断，不保证投资收益。
作者及同行资本不对因参考本内容造成的任何投资损失承担责任。
"""

files["09_runbooks/templates/daily_brief.md"] = """---
report_type: daily_brief
date: {date}
created_at: {datetime}
---

# 同行资本二级市场日报 — {date}

## 一、美股隔夜动态

### 核心标的变动

| Symbol | Close | Chg% | Key Signal |
|--------|-------|------|------------|
| NVDA | | | |
| TSLA | | | |
| AMD | | | |

### 对A+H影响预判

- 

## 二、A股+H股市场概况

### 主要指数

| Index | Close | Chg% |
|-------|-------|------|
| 上证指数 | | |
| 科创50 | | |
| 恒生科技 | | |

### SMR关注板块表现

| Sector | Chg% | Leading Stock |
|--------|------|---------------|
| 具身智能 | | |
| 半导体/算力 | | |
| 光模块/CPO | | |
| AI应用 | | |
| 量子 | | |

## 三、持仓盈亏

| Stock | Entry | Current | PnL% | Thesis Status |
|-------|-------|---------|------|---------------|
| | | | | |

## 四、风控状态

- 组合回撤: %
- 仓位分布: 
- 预警: 无 / 有

## 五、研究进展

- 

## 六、明日关注

- 

---

⚠️ 风险提示与免责声明

本内容仅供研究参考，不构成任何投资建议。股市有风险，投资需谨慎。
过往业绩不代表未来表现。请根据自身风险承受能力独立做出投资决策。
作者及同行资本不对因参考本内容造成的任何投资损失承担责任。
"""

# ============================================================
# Control Center files
# ============================================================

files["00_control/sector_priority_map.md"] = """# SMR 行业优先级地图

> 对齐VCR的sector_priority_map，只覆盖前沿科技赛道

## 三大行业板块

| Sector Key | 行业 | VCR优先级 | SMR定位 | 核心交易赛道 |
|-----------|------|----------|---------|------------|
| embodied_ai | 具身智能/机器人 | P0-core-build | 核心交易 | 整机+零部件 |
| semiconductor_compute | 半导体/算力芯片 | P1-priority-track | 核心交易 | GPU+光模块 |
| semiconductor_photonics | 半导体/光芯片CPO | P1-priority-track | 核心交易 | CPO+光引擎 |
| ai_agent | AI Agent/应用 | P1-priority-track | 观察池 | 应用+工作流 |
| quantum | 量子/前沿科学 | P1-priority-track | 前瞻观察 | 量子通信+计算 |

## 行业→美股对标映射

| 行业 | 美股对标 | 联动类型 |
|------|---------|---------|
| 光模块/CPO | NVDA, LITE, MRVL, COHR | 供应链映射 |
| 机器人零部件 | TSLA | 技术路线映射 |
| 量子 | IONQ, RGTI, QBTS | 估值锚映射 |
| 算力芯片 | NVDA, AMD, INTC, AVGO | 需求景气映射 |
| AI应用 | CRM, NOW, MSFT | 需求景气映射 |
"""

files["00_control/dispatch_board.md"] = """# SMR 调度面板

## 当前状态

- 数据管道: 🟡 待首次数据填充（需在正常终端运行 ah_daily_bar.py）
- Agent体系: ✅ 7个agent已注册
- Cron Job: ✅ 8个SMR cron job已配置
- 研究能力: 🟡 Skills已部署，待数据填充后验证

## 待办事项

- [ ] 在正常Mac终端运行: python3 /Users/apple/Documents/同行资本二级市场/08_scripts/data_harvester/ah_daily_bar.py --days 30
- [ ] 验证数据填充后因子计算是否正常
- [ ] 首次手动触发盘前简报测试

## 研究触发队列

| 日期 | 触发源 | 行业 | 状态 |
|------|--------|------|------|
| | | | |

## 风控预警

| 日期 | 预警类型 | 严重度 | 状态 |
|------|---------|--------|------|
| | | | |
"""

files["00_control/watchlist_registry.md"] = """# SMR 标的注册表

## A股标的

### 具身智能/机器人

| Code | Name | Sector | Pool | Added |
|------|------|--------|------|-------|
| 688017 | 绿的谐波 | embodied_ai | watchlist | 2026-04-09 |
| 300124 | 汇川技术 | embodied_ai | watchlist | 2026-04-09 |
| 601689 | 拓普集团 | embodied_ai | watchlist | 2026-04-09 |
| 002050 | 三花智控 | embodied_ai | watchlist | 2026-04-09 |
| 603728 | 鸣志电器 | embodied_ai | watchlist | 2026-04-09 |
| 002796 | 中大力德 | embodied_ai | watchlist | 2026-04-09 |
| 301368 | 丰立智能 | embodied_ai | watchlist | 2026-04-09 |
| 688322 | 奥比中光 | embodied_ai | watchlist | 2026-04-09 |
| 002600 | 领益智造 | embodied_ai | watchlist | 2026-04-09 |
| 600580 | 卧龙电驱 | embodied_ai | watchlist | 2026-04-09 |

### 半导体/算力

| Code | Name | Sector | Pool | Added |
|------|------|--------|------|-------|
| 688041 | 海光信息 | semiconductor_compute | watchlist | 2026-04-09 |
| 688256 | 寒武纪 | semiconductor_compute | watchlist | 2026-04-09 |
| 688008 | 澜起科技 | semiconductor_compute | watchlist | 2026-04-09 |
| 301269 | 华大九天 | semiconductor_compute | watchlist | 2026-04-09 |
| 688521 | 芯原股份 | semiconductor_compute | watchlist | 2026-04-09 |
| 603986 | 兆易创新 | semiconductor_compute | watchlist | 2026-04-09 |

### 光模块/CPO

| Code | Name | Sector | Pool | Added |
|------|------|--------|------|-------|
| 300308 | 中际旭创 | semiconductor_photonics | watchlist | 2026-04-09 |
| 300502 | 新易盛 | semiconductor_photonics | watchlist | 2026-04-09 |
| 300394 | 天孚通信 | semiconductor_photonics | watchlist | 2026-04-09 |
| 002281 | 光迅科技 | semiconductor_photonics | watchlist | 2026-04-09 |
| 300620 | 光库科技 | semiconductor_photonics | watchlist | 2026-04-09 |
| 872808 | 曙光数创 | semiconductor_photonics | watchlist | 2026-04-09 |
| 002837 | 英维克 | semiconductor_photonics | watchlist | 2026-04-09 |

### AI应用

| Code | Name | Sector | Pool | Added |
|------|------|--------|------|-------|
| 002230 | 科大讯飞 | ai_agent | watchlist | 2026-04-09 |
| 688111 | 金山办公 | ai_agent | watchlist | 2026-04-09 |
| 603039 | 泛微网络 | ai_agent | watchlist | 2026-04-09 |

### 量子

| Code | Name | Sector | Pool | Added |
|------|------|--------|------|-------|
| 688027 | 国盾量子 | quantum | watchlist | 2026-04-09 |

## H股标的

| Code | Name | Sector | Pool | Added |
|------|------|--------|------|-------|
| 09980 | 优必选 | embodied_ai | watchlist | 2026-04-09 |
| 00020 | 商汤-W | ai_agent | watchlist | 2026-04-09 |
| 00981 | 中芯国际 | semiconductor_compute | watchlist | 2026-04-09 |
| 01347 | 华虹半导体 | semiconductor_compute | watchlist | 2026-04-09 |

## 美股对标（仅跟踪，不投资）

| Symbol | Name | Sector | Added |
|--------|------|--------|-------|
| NVDA | 英伟达 | semiconductor_compute | 2026-04-09 |
| AMD | 超微半导体 | semiconductor_compute | 2026-04-09 |
| INTC | 英特尔 | semiconductor_compute | 2026-04-09 |
| AVGO | 博通 | semiconductor_compute | 2026-04-09 |
| LITE | Lumentum | semiconductor_photonics | 2026-04-09 |
| MRVL | Marvell | semiconductor_photonics | 2026-04-09 |
| COHR | Coherent | semiconductor_photonics | 2026-04-09 |
| VRT | Vertiv | semiconductor_photonics | 2026-04-09 |
| TSLA | 特斯拉 | embodied_ai | 2026-04-09 |
| IONQ | IonQ | quantum | 2026-04-09 |
| RGTI | Rigetti | quantum | 2026-04-09 |
| QBTS | D-Wave | quantum | 2026-04-09 |
| CRM | Salesforce | ai_agent | 2026-04-09 |
| NOW | ServiceNow | ai_agent | 2026-04-09 |
| MSFT | 微软 | ai_agent | 2026-04-09 |
| MU | 美光 | semiconductor_compute | 2026-04-09 |
| SNPS | Synopsys | semiconductor_compute | 2026-04-09 |
| CDNS | Cadence | semiconductor_compute | 2026-04-09 |
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
