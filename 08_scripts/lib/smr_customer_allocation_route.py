#!/usr/bin/env python3
"""Confirmed customer-allocation route checks for Phase 41."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_specific_evidence_request import list_specific_evidence_requests
from smr_wiki import now_ts


def build_customer_allocation_route(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    requests = [
        row
        for row in list_specific_evidence_requests(conn, ticker=ticker)
        if row.get("evidence_type") == "confirmed_customer_allocation"
    ]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "customer_allocation_route": {
            "status": "proxy_only",
            "confirmed_customer_allocation_available": False,
            "customer_allocation_confirmed": False,
            "specific_request_open": bool(requests),
            "proxy_evidence_available": True,
            "proxy_allowed_usage": "bear_case_context_or_scenario_support",
            "route_rows": [
                {
                    "route_type": "customer_side_public_statement",
                    "availability": "unknown",
                    "allowed_usage": "supporting_evidence_if_traceable",
                },
                {
                    "route_type": "proxy_only",
                    "availability": "available",
                    "allowed_usage": "scenario_analysis_only",
                },
                {
                    "route_type": "manual_research_required",
                    "availability": "required",
                    "allowed_usage": "route_check_only",
                },
            ],
            "do_not_do": [
                "do not treat customer proxy as confirmed allocation",
                "do not infer NVIDIA allocation from North America customer references",
                "do not treat order visibility as confirmed customer allocation",
            ],
        },
        "safety": {
            "evidence_written": False,
            "customer_allocation_confirmed": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }
