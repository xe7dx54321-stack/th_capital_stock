#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_watchlist_intelligence_aggregator import aggregate_intelligence
from smr_human_readable_thesis_summary import build_thesis_summary
from smr_tracking_decision_classifier import build_decision

def build_analyst_detail(ticker="300308.SZ"):
    agg = aggregate_intelligence(ticker); a = agg.get("watchlist_intelligence_aggregator", {})
    thesis = build_thesis_summary(ticker); h = thesis.get("human_thesis_summary", {})
    decision = build_decision(ticker); td = decision.get("tracking_decision", {})
    supported = [{"variable": v, "status": "tracking-support"} for v in a.get("key_supported_variables", [])]
    unconfirmed = [{"variable": "official_consensus", "status": "unconfirmed"},
                   {"variable": "supplier_share", "status": "scenario-only"},
                   {"variable": "customer_allocation", "status": "proxy-only"},
                   {"variable": "valuation_boundary", "status": "scenario-bound"}]
    review_items = [f"{a.get('review_required_candidates',0)} 条敏感变量 candidate 仍需人工复核。",
                    "禁止直接确认 customer allocation。",
                    "禁止由此生成 pending 或 order。"]
    next_events = h.get("next_observation_focus", [])[:5]
    boundary = ["continue_tracking 不是买入信号。",
                "tracking-support 不是 confirmed evidence。",
                "当前不进入 pending，不生成 order，不触发 trade。"]
    return {"ticker": ticker, "analyst_detail": {
        "supported_variables": supported, "unconfirmed_variables": unconfirmed,
        "review_required": review_items, "next_events": next_events,
        "boundary": boundary, "tracking_decision": td.get("decision", ""),
        "thesis_score": a.get("thesis_strength_score", 0)
    }}
