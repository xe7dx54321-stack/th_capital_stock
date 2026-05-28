#!/usr/bin/env python3
"""Supplier-share scenario assumption registry for Phase 42."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_supplier_share_route import build_supplier_share_route
from smr_wiki import now_ts


def scenario_id_for(ticker: str, scenario_name: str = "base") -> str:
    code = normalize_ticker(ticker).split(".")[0].lower()
    return f"supplier_share_scenario_{code}_{scenario_name}"


def build_supplier_share_scenario_registry(
    conn: sqlite3.Connection,
    ticker: str = TARGET_REVIEW_TICKER,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    route = build_supplier_share_route(conn, ticker).get("supplier_share_route") or {}
    scenario = {
        "ticker": ticker,
        "scenario_id": scenario_id_for(ticker),
        "scenario_type": "supplier_share_assumption",
        "value_type": "range_or_qualitative",
        "value": "unknown_or_range_placeholder",
        "confidence": "low",
        "allowed_usage": "scenario_analysis_only",
        "is_confirmed": False,
        "source_basis": "manual_research_required",
        "route_status": route.get("status") or "not_publicly_confirmable",
        "caveats": [
            "not publicly confirmed",
            "do not treat as fact",
            "requires explicit scenario labeling",
        ],
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "supplier_share_scenario_registry": {
            "scenario_count": 1,
            "confirmed_scenarios": 0,
            "promotion_gate_eligible": False,
            "scenarios": [scenario],
        },
        "safety": {
            "supplier_share_confirmed": False,
            "evidence_written": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }
