#!/usr/bin/env python3
"""Phase 45 final thesis validity review."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_final_research_asset_aggregator import (
    REMAINING_CORE_GAPS,
    STRENGTHENED_VARIABLES,
    build_final_research_asset_summary,
)
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


PRIMARY_THESIS = (
    "AI optical interconnect demand may support higher-value product mix and "
    "shipment/order visibility for 300308.SZ."
)


def build_final_thesis_review(
    conn: sqlite3.Connection,
    ticker: str = TARGET_REVIEW_TICKER,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    assets = build_final_research_asset_summary(conn, ticker).get("final_research_asset_summary") or {}
    supported = [f"{variable} evidence strengthened" for variable in STRENGTHENED_VARIABLES]
    not_supported = [
        "confirmed supplier share",
        "confirmed official consensus benchmark",
        "confirmed customer allocation",
    ]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "final_thesis_review": {
            "primary_thesis": PRIMARY_THESIS,
            "thesis_status": "research_supported_but_not_investment_ready",
            "thesis_confidence": "medium",
            "what_is_supported": supported,
            "what_is_not_supported": not_supported,
            "scenario_dependency": "high",
            "key_uncertainties": list(REMAINING_CORE_GAPS),
            "bear_case_pressure": "partially_mitigated_but_not_cleared",
            "valuation_boundary": "scenario_analysis_only",
            "conclusion_readiness": "formal_research_conclusion_possible",
            "investment_readiness": "not_ready",
            "asset_context": {
                "manual_candidate_closeout": (assets.get("evidence_chain") or {}).get("manual_candidates_reviewed", 0),
                "remaining_core_gaps": assets.get("remaining_core_gaps") or list(REMAINING_CORE_GAPS),
            },
        },
        "safety": {
            "research_conclusion_is_investment_advice": False,
            "trade_recommendation_generated": False,
            "target_price_generated": False,
            "position_guidance_generated": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }
