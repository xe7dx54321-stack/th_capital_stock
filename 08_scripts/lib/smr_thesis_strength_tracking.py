#!/usr/bin/env python3
"""Phase 46 thesis strength tracking score."""

from __future__ import annotations

from typing import Any

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


SCORE_COMPONENTS = {
    "product_mix_support": 10,
    "order_visibility_support": 8,
    "shipment_support": 9,
    "ASP_price_proxy_support": 5,
    "official_consensus_status": -8,
    "supplier_share_scenario_quality": -6,
    "customer_allocation_proxy_quality": -5,
    "bear_case_residual_risk": -4,
    "valuation_boundary_quality": -3,
    "evidence_quality": 6,
}


def build_thesis_strength_tracking(ticker: str = TARGET_REVIEW_TICKER) -> dict[str, Any]:
    positive = ["product_mix_support", "order_visibility_support", "shipment_support"]
    negative = [
        "official_consensus_status",
        "supplier_share_scenario_quality",
        "customer_allocation_proxy_quality",
    ]
    return {
        "generated_at": now_ts(),
        "ticker": normalize_ticker(ticker),
        "thesis_strength_tracking": {
            "thesis_strength_score": 62,
            "thesis_strength_bucket": "watchlist_positive_but_unconfirmed",
            "score_delta_from_phase45": "baseline",
            "score_components": dict(SCORE_COMPONENTS),
            "positive_contributors": positive,
            "negative_or_unconfirmed_contributors": negative,
            "allowed_interpretation": "research_tracking_only",
            "forbidden_interpretation": [
                "buy_signal",
                "pending_approval",
                "paper_order",
            ],
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
        },
        "safety": {
            "score_is_buy_signal": False,
            "score_triggers_pending": False,
            "score_triggers_order": False,
            "confidence_bucket_high": False,
        },
    }
