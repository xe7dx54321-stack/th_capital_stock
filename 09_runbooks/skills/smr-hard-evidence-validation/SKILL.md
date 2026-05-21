---
name: smr-hard-evidence-validation
description: Use when an SMR analyst, report writer, or research agent evaluates hard evidence for a secondary-market thesis, especially customer capex, order visibility, shipments, margins, pricing, competition, valuation, consensus/divergence, or any key variable that could decide a buy/sell/rotation action. Requires separating facts from inference, grading source strength, and converting missing hard evidence into explicit follow-up research tasks.
---

# smr-hard-evidence-validation

Use this skill before a thesis treats an industry or company variable as a reason to buy, sell, add, reduce, or rotate. It turns "we should check capex/orders/margins/competition" into a repeatable research discipline.

## Boundary

- Do not treat sell-side ratings, target prices, or earnings forecasts as hard evidence by themselves.
- Do not write a key variable as confirmed unless it is backed by first-party, customer, competitor, industry, or traceable market data.
- Do not hide missing evidence. If a decisive variable is not anchored, mark it as `待补证据` and create a follow-up task.
- Do not confuse methodology with conclusion. A framework can tell the agent what to look for; only sources can prove a fact.

## Evidence Ladder

1. **Hard evidence**: company filings, earnings releases, investor presentations, official transcripts, exchange disclosures, customer/competitor filings, disclosed capex, backlog/orders, shipment data, ASP/pricing data, audited margins, reputable industry datasets.
2. **Strong supporting evidence**: management Q&A, supplier/customer read-through, conference notes with explicit data, multiple independent sell-side reports that cite the same underlying fact.
3. **Soft supporting evidence**: single sell-side estimate, news articles, expert commentary, channel checks without raw details, unsourced consensus language.
4. **Weak evidence**: social posts, generic narrative, valuation targets without assumptions, price action without fundamental support.

## Variable Workflow

For each key thesis variable:

1. Name the variable precisely: e.g. `US hyperscaler capex growth`, `800G/1.6T order visibility`, `gross margin expansion`, `competitive pricing pressure`.
2. State why it matters to the action: earnings surprise, valuation rerating, downside protection, position sizing, or exit trigger.
3. List available evidence by source type and date.
4. Decide whether the evidence is enough to support a conclusion:
   - `可确认`: hard evidence directly anchors the variable.
   - `可支持但未确认`: several sources support it, but first-party or hard data is missing.
   - `待补证据`: the report relies on the variable but current source pack lacks direct anchors.
5. If `待补证据`, write a concrete research task with source priority, accepted evidence, and how the result would change the thesis.

## Minimum Hard-Evidence Tests

Use these tests when the variable appears in a thesis or report:

- **Customer capex**: cite cloud/customer filings or calls, capex guidance, AI infrastructure commentary, and customer mix/read-through. Sell-side commentary is not enough.
- **Orders and shipment visibility**: cite backlog/order commentary, shipment mix, customer concentration, product ramp status, channel checks with dates, or supply-chain production evidence.
- **Margin and yield**: cite gross margin/operating margin trend, product mix, cost/yield language, ASP trend, capacity utilization, or peer margin comparison.
- **Competition and pricing**: cite competitor product/capacity updates, price cuts, share shifts, customer dual-sourcing, technology roadmap, or management discussion of competition.
- **Valuation and target range**: cite scenario assumptions, multiples, earnings assumptions, consensus spread, and downside case; do not use a target price alone.

See `references/hard-evidence-map.md` for the variable-to-source matrix and accepted task format.

## Output Requirements

Any agent using this skill must produce:

1. `key_variable_audit`: variable, current evidence, source strength, gap status, thesis impact.
2. `evidence_gap_tasks`: only for missing or weakly anchored key variables.
3. `thesis_effect`: what happens to action, sizing, entry, exit, or confidence if the evidence confirms or refutes the variable.

The full investment report may summarize these tasks, but the underlying report must preserve the distinction among facts, inferences, judgments, and missing evidence.
