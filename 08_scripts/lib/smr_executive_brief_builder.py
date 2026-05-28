#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_watchlist_intelligence_aggregator import aggregate_intelligence
from smr_human_readable_thesis_summary import build_thesis_summary

def build_executive(ticker="300308.SZ"):
    agg = aggregate_intelligence(ticker); a = agg.get("watchlist_intelligence_aggregator", {})
    thesis = build_thesis_summary(ticker); h = thesis.get("human_thesis_summary", {})
    conclusion = ["继续跟踪。", "thesis 仍偏正向，但未达到 pending 条件。", "本期没有触发 order/trade。"]
    changes = [f"tracking-support 候选证据已有 {a.get('tracking_support_candidates',0)} 条。",
               f"{a.get('review_required_candidates',0)} 条敏感变量仍需复核。",
               f"thesis_score 维持 {a.get('thesis_strength_score',0)}。"]
    support = [f"{', '.join(a.get('key_supported_variables',['N/A']))} 有 tracking-support 支撑。",
               "真实来源正文已进入 candidate 链路。"]
    blockers = h.get("why_not_pending", [])[:3]
    next_steps = h.get("next_observation_focus", [])[:3]
    return {"ticker": ticker, "executive_brief": {
        "conclusion": conclusion, "changes": changes, "support": support,
        "blockers": blockers, "next_steps": next_steps,
        "forbidden_note": "仅用于 watchlist tracking，不构成投资建议。"
    }}
