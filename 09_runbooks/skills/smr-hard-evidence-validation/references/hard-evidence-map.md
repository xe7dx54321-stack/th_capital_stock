# Hard Evidence Map

Use this matrix when a thesis depends on a variable that must be verified beyond sell-side conclusions.

| Variable | Priority Sources | Accepted Evidence | Report Use | If Missing |
|---|---|---|---|---|
| Customer capex / cloud capex | Customer filings and calls; capex guidance; hyperscaler earnings decks; supplier read-through; reputable industry capex datasets | disclosed capex, guided capex direction, AI infrastructure commentary, datacenter spend mix, customer order/read-through with date | support demand durability and earnings-surprise assumptions | mark `待补证据`; do not call demand durability confirmed |
| Orders / shipments / backlog | Company IR, exchange Q&A, earnings calls, order/backlog disclosures, shipment mix, channel checks with dates | order visibility, backlog, customer concentration, product ramp, shipment share, production allocation | support near-term revenue visibility and sizing | downgrade to hypothesis; create task to verify order durability |
| Margin / yield / ASP | Financial statements, gross margin bridge, management commentary, peer margin data, pricing surveys | gross margin trend, product mix, yield/cost commentary, ASP movement, capacity utilization | support profit elasticity and model assumptions | keep margin expansion as assumption, not conclusion |
| Competition / capacity / pricing | Competitor filings, product roadmap, capex/capacity expansion, pricing news, customer dual-sourcing | competitor ramp, price pressure, share shift, technology gap, customer sourcing pattern | support moat or risk assessment | require bear-case expansion and lower confidence |
| Valuation / target / consensus | Multiple sell-side models, consensus databases, scenario model, peer multiples, historical range | EPS/revenue assumptions, multiple range, scenario implied return, target dispersion | support risk/reward and priced-in discussion | avoid target-price-driven conclusion |
| Technical / flow support | Price/volume data, factor snapshots, strategy backtest, capital flow, risk alerts | signal definition, sample size, win rate, average return, invalidation level, flow confirmation | timing and risk-control support only | cannot replace fundamental evidence |

## Evidence Gap Task Format

Each missing hard-evidence variable should become a task:

```json
{
  "variable_id": "customer_capex",
  "variable_label": "云厂商资本开支 / 客户 capex",
  "priority": "P0",
  "research_question": "云厂商 AI capex 是否足以支撑本次调入腿的需求持续性假设？",
  "source_priority": ["official_customer_filings", "earnings_call_transcripts", "company_ir", "industry_data", "sell_side_cross_check"],
  "accepted_evidence": ["客户 capex 指引或实际值", "管理层关于 AI 基建投资的原话", "供应商订单/出货/客户结构锚点"],
  "thesis_effect": "若证实 capex 上修且订单能见度延续，可提高需求持续性置信度；若 capex 放缓或客户延后订单，调入腿需要降仓或推迟。"
}
```

## Source Discipline

- A single report saying "buy" or "target price up" is a source opinion, not a fact.
- A fact can support multiple interpretations; reports must state the interpretation separately.
- Consensus is useful mainly because it reveals what may already be priced in.
- Divergence is useful only after the agent explains why one side is more likely to be right.
