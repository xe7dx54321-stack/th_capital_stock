#!/usr/bin/env python3
"""Supplier-share evidence route checks for Phase 41."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_specific_evidence_request import list_specific_evidence_requests
from smr_wiki import now_ts


def build_supplier_share_route(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    requests = [
        row
        for row in list_specific_evidence_requests(conn, ticker=ticker)
        if row.get("evidence_type") == "supplier_share"
    ]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "supplier_share_route": {
            "status": "not_publicly_confirmable",
            "confirmed_supplier_share_available": False,
            "supplier_share_confirmed": False,
            "specific_request_open": bool(requests),
            "recommended_usage": "scenario_analysis_only",
            "route_rows": [
                {
                    "route_type": "company_direct_disclosure",
                    "availability": "unlikely",
                    "allowed_usage": "confirmed_if_directly_disclosed_only",
                },
                {
                    "route_type": "customer_direct_disclosure",
                    "availability": "unknown",
                    "allowed_usage": "supporting_evidence_if_traceable",
                },
                {
                    "route_type": "scenario_assumption_only",
                    "availability": "available",
                    "allowed_usage": "scenario_analysis_only",
                    "caveat": "must be explicitly marked as assumption",
                },
            ],
            "do_not_do": [
                "do not infer exact share from general demand",
                "do not convert customer proxy into supplier share",
                "do not mark scenario assumption as confirmed",
            ],
        },
        "safety": {
            "evidence_written": False,
            "supplier_share_confirmed": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }
