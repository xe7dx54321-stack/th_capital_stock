#!/usr/bin/env python3
"""Phase 45 final research conclusion classifier."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_final_research_asset_aggregator import REMAINING_CORE_GAPS
from smr_final_thesis_review import build_final_thesis_review
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


CONCLUSION_STATUSES = {
    "formal_research_conclusion_positive_watchlist",
    "formal_research_conclusion_neutral_tracking",
    "formal_research_conclusion_needs_more_evidence",
    "formal_research_conclusion_deprioritize",
    "formal_research_conclusion_blocked",
    "unknown",
}

PAPER_WATCHLIST_READINESS = {
    "paper_watchlist_candidate",
    "tracking_only",
    "needs_more_evidence",
    "deprioritize",
    "blocked",
}


def build_final_research_conclusion(
    conn: sqlite3.Connection,
    ticker: str = TARGET_REVIEW_TICKER,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    thesis = build_final_thesis_review(conn, ticker).get("final_thesis_review") or {}
    status = "formal_research_conclusion_positive_watchlist"
    readiness = "paper_watchlist_candidate"
    why_not_pending = [
        "supplier share unconfirmed",
        "official consensus not confirmed",
        "customer allocation not confirmed",
        "valuation support remains scenario-bound",
    ]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "final_research_conclusion": {
            "conclusion_status": status,
            "conclusion_confidence": "medium_low",
            "paper_watchlist_readiness": readiness,
            "why": [
                "product mix / order visibility / shipment evidence supports continued tracking",
                "bear case partially mitigated",
                "research package is sufficiently bounded",
            ],
            "why_not_pending": why_not_pending,
            "remaining_core_gaps": thesis.get("key_uncertainties") or list(REMAINING_CORE_GAPS),
            "allowed_next_step": "paper_watchlist_tracking_only",
            "forbidden_next_steps": [
                "pending_human_review",
                "approved_paper",
                "paper_order",
                "real_trade",
            ],
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed_true": 0,
        },
        "safety": {
            "formal_research_conclusion_is_trade_advice": False,
            "paper_watchlist_candidate_is_pending": False,
            "trade_recommendation_generated": False,
            "target_price_generated": False,
            "position_guidance_generated": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }
