#!/usr/bin/env python3
"""Official consensus availability checks for Phase 41."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_specific_evidence_request import list_specific_evidence_requests
from smr_wiki import now_ts


def build_official_consensus_availability(
    conn: sqlite3.Connection,
    ticker: str = TARGET_REVIEW_TICKER,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    requests = [
        row
        for row in list_specific_evidence_requests(conn, ticker=ticker)
        if row.get("evidence_type") == "official_consensus"
    ]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "official_consensus_availability": {
            "status": "commercial_source_required",
            "official_consensus_available": False,
            "official_consensus_confirmed": False,
            "specific_request_open": bool(requests),
            "internal_proxy_available": True,
            "internal_proxy_allowed_usage": "supporting_context_only",
            "authorized_source_routes": [
                {
                    "route_type": "authorized_sell_side_source",
                    "status": "planned",
                    "limitation": "requires licensed or authorized data",
                },
                {
                    "route_type": "commercial_consensus_provider",
                    "status": "planned",
                    "limitation": "not currently implemented",
                },
            ],
            "do_not_do": [
                "do not treat internal proxy as official consensus",
                "do not infer consensus from management commentary",
                "do not scrape restricted consensus data",
            ],
        },
        "safety": {
            "evidence_written": False,
            "official_consensus_confirmed": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }
