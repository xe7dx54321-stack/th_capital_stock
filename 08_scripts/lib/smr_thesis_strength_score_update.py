#!/usr/bin/env python3
"""Phase 47 thesis strength score update for periodic watchlist review."""

from __future__ import annotations

from typing import Any

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_thesis_strength_tracking import build_thesis_strength_tracking, SCORE_COMPONENTS
from smr_wiki import now_ts


def build_thesis_strength_update(
    ticker: str = TARGET_REVIEW_TICKER,
    *,
    thesis_delta: str = "unchanged",
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    previous = build_thesis_strength_tracking(ticker).get("thesis_strength_tracking") or {}
    previous_score = previous.get("thesis_strength_score", 62)
    previous_bucket = previous.get("thesis_strength_bucket", "watchlist_positive_but_unconfirmed")
    current_score = previous_score
    if thesis_delta == "strengthened":
        current_score = min(previous_score + 5, 85)
    elif thesis_delta == "weakened":
        current_score = max(previous_score - 5, 20)
    score_delta = current_score - previous_score
    current_bucket = previous_bucket
    if current_score >= 75:
        current_bucket = "watchlist_confirmed_positive"
    elif current_score >= 55:
        current_bucket = "watchlist_positive_but_unconfirmed"
    elif current_score >= 35:
        current_bucket = "watchlist_neutral_needs_evidence"
    else:
        current_bucket = "watchlist_negative_or_archival_candidate"
    positive = [
        "product_mix_support",
        "order_visibility_support",
        "shipment_support",
    ]
    negative = [
        "official_consensus_status",
        "supplier_share_scenario_quality",
        "customer_allocation_proxy_quality",
    ]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "thesis_strength_update": {
            "previous_score": previous_score,
            "current_score": current_score,
            "score_delta": score_delta,
            "previous_bucket": previous_bucket,
            "current_bucket": current_bucket,
            "thesis_delta": thesis_delta,
            "positive_contributors": positive,
            "unconfirmed_or_negative_contributors": negative,
            "allowed_interpretation": "research_tracking_only",
            "forbidden_interpretation": [
                "buy_signal",
                "pending_approval",
                "paper_order",
            ],
        },
        "safety": {
            "score_delta_is_buy_signal": False,
            "score_delta_triggers_pending": False,
            "score_delta_triggers_order": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
        },
    }
