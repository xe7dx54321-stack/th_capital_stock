---
name: smr-investment-report-writing
description: "Use when writing full SMR investment reports, portfolio action reports, buy/sell strategy reports, IC memos, or dashboard-readable deep reports from research synthesis, evidence packs, technical evidence, risk cards, and portfolio context. Requires an institutional investment-bank style: conclusion-first, variant view, consensus/divergence, evidence chain, scenario analysis, valuation, execution plan, risks, and falsification; never writes a report as a loose summary of system cards."
---

# smr-investment-report-writing

Use this skill after `smr-research-synthesis` has produced or guided the research judgment. This skill turns fragmented evidence and analysis into a complete report that can support a buy, sell, reduce, add, or watch decision.

## Boundary

- Do not write a report by stitching together dashboard cards.
- Do not hide uncertainty with polished language.
- Do not state a buy/sell conclusion without a variant view, evidence chain, risk/reward, and falsification plan.
- Do not use system state as report content unless it explains evidence quality.
- Do not copy the style or text of any external report.

## Report Spine

Every full report must follow this spine:

1. **Title and conclusion**: the action, confidence, horizon, and one-sentence reason.
2. **Investment question**: the market question the report is answering.
3. **Variant view**: what SMR believes is different from consensus.
4. **Consensus map**: what the market and external sources broadly agree on.
5. **Divergence map**: the variables where serious disagreement exists.
6. **SMR judgment**: which side of each key divergence SMR takes and why.
7. **Evidence chain**: first-party data, industry data, external research, calls, news, technical/flow evidence.
8. **Valuation and scenario**: base/upside/downside assumptions, not only target price.
9. **Portfolio action**: what to do, sizing logic, entry/exit/stop/add/reduce conditions.
10. **Risks and falsification**: what would prove the thesis wrong and how quickly to react.
11. **Follow-up plan**: next evidence dates, open questions, and monitoring triggers.

## Writing Rules

- Start with the decision, then prove it.
- Separate fact, inference, and judgment.
- Treat consensus as what may already be priced in.
- Treat divergence as the possible source of alpha.
- Name the key variable that will decide whether the thesis works.
- Include the strongest bear case before finalizing the recommendation.
- If the evidence packet is incomplete, write a lower-confidence report and explicitly list missing research tasks.
- Use tables for evidence maps, scenario assumptions, and action plans.
- Keep dashboard-facing summaries concise, but keep the full report rigorous.
- Apply `../smr-hard-evidence-validation/SKILL.md` whenever the report relies on customer capex, orders, shipments, margin/yield, competition, pricing, or valuation. Missing hard evidence must appear in `evidence_gap_tasks` and in the follow-up plan, not as a disguised conclusion.

## Required Sections

### 1. Executive Summary

Include:

- action: buy / add / hold / reduce / sell / watch
- confidence: high / medium / low / hypothesis only
- horizon: days / weeks / months / quarters
- expected payoff source: earnings surprise, valuation rerating, mean reversion, risk reduction, liquidity, or technical timing

### 2. Core Thesis

Write the exact bet:

- What has to be true?
- What is the market likely assuming?
- What does SMR think the market is missing?
- What evidence would change our mind?

### 3. Consensus And Divergence

Use a table:

| Variable | Consensus | Divergence | SMR View | Why It Matters |
|---|---|---|---|---|

Variables may include demand, price, capex, margin, customer, supply, competitive position, valuation, catalyst timing, regulatory/policy risk.

### 4. Evidence Chain

Use a table:

| Evidence | Source Type | What It Supports | What It Does Not Prove | Confidence |
|---|---|---|---|---|

Source types: official material, earnings call, external research, industry data, competitor read-through, market data, technical signal, capital flow, risk alert.

### 5. Scenario And Valuation

Do not rely only on target price. Show scenario assumptions:

| Scenario | Key Assumption | Expected Stock Implication | Probability | Trigger |
|---|---|---:|---:|---|

### 6. Portfolio Action Plan

Show:

- initial action
- add condition
- reduce condition
- exit condition
- stop/invalidating level
- maximum position implication
- what to monitor after execution

## Output Contract

The report writer should output both:

1. `report_markdown`: full report suitable for `/artifact`.
2. `report_summary_json`: structured fields for dashboard and later review:
   - `action`
   - `confidence`
   - `variant_view`
   - `consensus_points`
   - `divergence_points`
   - `smr_judgment`
   - `evidence_chain`
   - `scenario_analysis`
   - `portfolio_action_plan`
   - `kill_triggers`
   - `follow_up_tasks`
   - `evidence_gap_tasks`

## References

Read `references/report-template.md` when writing the final report.
