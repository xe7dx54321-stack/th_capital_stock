---
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
