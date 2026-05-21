---
name: smr-research-synthesis
description: Use when producing secondary-market research, stock reports, rotation logic, portfolio action memos, thesis checks, or recommendation narratives from sell-side reports, earnings calls, filings, official materials, news, factor data, or technical evidence. Requires multi-source synthesis, consensus/divergence analysis, original judgment, evidence grading, and falsification conditions; never treats a single report or source as the system conclusion.
---

# smr-research-synthesis

Use this skill whenever SMR turns raw materials into a research judgment or action rationale.

## Boundary

- Do not copy a sell-side report's conclusion as SMR's conclusion.
- Do not upgrade price action, one report, one news article, or one management quote into a high-conviction view.
- Do not hide missing evidence. Name the gap and downgrade confidence.
- Do not produce real trade instructions; produce a research judgment and decision support.

## Research Standard

Before writing a conclusion, build a source map:

1. Sell-side and external research: read at least 3 reports from at least 2 institutions when available.
2. Official first-party materials: filings, earnings releases, investor presentations, IR activity records, exchange disclosures.
3. Management voice: earnings calls, public transcripts, investor relations Q&A, conference summaries.
4. Industry data: demand, price, inventory, capex, utilization, market share, customer orders, policy, competitor movement.
5. Market evidence: price trend, volume, relative strength, valuation, flows, options/short interest when available.
6. Counter-evidence: bearish reports, missed guidance, margin pressure, inventory risk, valuation crowding, technical overheat.

If the source map is incomplete, label the output as `素材型假设` or `中等置信假设`, not as a research conclusion.

## Synthesis Workflow

1. Extract the core claim from each source.
2. Normalize claims into comparable drivers: demand, pricing, share, margin, capex, customer, product cycle, valuation, risk.
3. Identify consensus: what multiple sources independently agree on.
4. Identify divergence: what differs across sources, models, assumptions, target prices, time horizons, or risk emphasis.
5. Cross-check against first-party material and hard data.
6. Form SMR's own thesis: what we believe, why, over what horizon, and what market expectation we think is wrong.
7. Define falsification: what evidence would prove the thesis wrong.
8. Translate into action only after confidence, risk/reward, and portfolio impact are explicit.

## Hard Evidence Discipline

When a thesis relies on customer capex, order visibility, shipments, margin/yield, competition, pricing, or valuation, apply `../smr-hard-evidence-validation/SKILL.md`.

- Treat these variables as research variables, not as simple data-fetch keywords.
- If a key variable lacks first-party, customer, competitor, industry, or traceable market data, mark it as `待补证据`.
- Convert each missing key variable into an `evidence_gap_tasks` item with source priority, acceptance criteria, and thesis impact.
- Do not let a sell-side conclusion substitute for hard evidence.

## Required Output Shape

Every research or action rationale must include:

1. **Conclusion first**: buy/add/watch/reduce/avoid, plus confidence level.
2. **What we are betting on**: the precise business or market assumption.
3. **Consensus evidence**: 3-5 points that survive cross-source comparison.
4. **Divergence and debate**: where sources disagree and why it matters.
5. **First-party verification**: what filings/calls/official materials confirm or contradict.
6. **Industry data**: the key data points that validate the thesis.
7. **Valuation and expectation**: what is already priced in and where surprise may come from.
8. **Technical/flow evidence**: only as timing and risk-control support, not the core thesis.
9. **Falsification and follow-up**: what to watch, when to add, when to cut, when to admit the thesis failed.

## Evidence Grades

- `可形成研究判断`: at least 3 external research samples, at least 2 institutions, first-party material, and either fresh management voice or hard industry data.
- `中等置信假设`: at least 2 external samples plus one first-party or hard data anchor.
- `素材型假设`: fewer than 2 independent research samples, missing first-party material, or no management/industry verification.
- `价格信号`: mostly technical or flow evidence; cannot support a fundamental conclusion.

## References

Read `references/institutional-report-standard.md` when writing or revising report templates, agent prompts, or dashboard report language.
