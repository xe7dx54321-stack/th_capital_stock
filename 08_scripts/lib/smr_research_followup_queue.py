#!/usr/bin/env python3
"""Research follow-up queue for Phase 41 specific evidence tasks."""

from __future__ import annotations

import sqlite3
from collections import Counter
from typing import Any

from smr_customer_allocation_route import build_customer_allocation_route
from smr_official_consensus_availability import build_official_consensus_availability
from smr_research_review_lifecycle import REPAIR_ONLY_TICKER, TARGET_REVIEW_TICKER, normalize_ticker
from smr_specific_evidence_request import list_specific_evidence_requests
from smr_supplier_share_route import build_supplier_share_route
from smr_wiki import now_ts


CORE_EVIDENCE_TYPES = ["official_consensus", "supplier_share", "confirmed_customer_allocation"]

ITEM_TYPE_BY_EVIDENCE_TYPE = {
    "official_consensus": "OFFICIAL_CONSENSUS_SOURCE_CHECK",
    "supplier_share": "SUPPLIER_SHARE_ROUTE_CHECK",
    "confirmed_customer_allocation": "CUSTOMER_ALLOCATION_ROUTE_CHECK",
    "ASP_price_proxy": "SPECIFIC_EVIDENCE_REQUEST",
    "customer_side_signal": "SPECIFIC_EVIDENCE_REQUEST",
    "industry_forecast": "SPECIFIC_EVIDENCE_REQUEST",
    "bear_case_evidence": "SPECIFIC_EVIDENCE_REQUEST",
}

ALLOWED_USAGE_BY_EVIDENCE_TYPE = {
    "official_consensus": "expectation_gap_benchmark_if_authorized",
    "supplier_share": "scenario_analysis_only",
    "confirmed_customer_allocation": "scenario_analysis_only",
    "ASP_price_proxy": "valuation_support",
    "customer_side_signal": "supporting_evidence",
    "industry_forecast": "supporting_context_only",
    "bear_case_evidence": "bear_case_context",
}


def followup_item_id_for(ticker: str, evidence_type: str) -> str:
    return f"followup_{normalize_ticker(ticker).split('.')[0].lower()}_{evidence_type}"


def _route_context(conn: sqlite3.Connection, ticker: str, evidence_type: str) -> dict[str, Any]:
    if evidence_type == "official_consensus":
        body = build_official_consensus_availability(conn, ticker).get("official_consensus_availability") or {}
        return {"status": body.get("status"), "do_not_do": body.get("do_not_do") or []}
    if evidence_type == "supplier_share":
        body = build_supplier_share_route(conn, ticker).get("supplier_share_route") or {}
        return {"status": body.get("status"), "do_not_do": body.get("do_not_do") or []}
    if evidence_type == "confirmed_customer_allocation":
        body = build_customer_allocation_route(conn, ticker).get("customer_allocation_route") or {}
        return {"status": body.get("status"), "do_not_do": body.get("do_not_do") or []}
    return {"status": "specific_request_open", "do_not_do": []}


def build_research_followup_queue(conn: sqlite3.Connection, ticker: str | None = None) -> dict[str, Any]:
    ticker_value = normalize_ticker(ticker or TARGET_REVIEW_TICKER)
    items: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    if ticker_value == REPAIR_ONLY_TICKER:
        excluded_rows.append({"ticker": ticker_value, "reason": "repair_required_before_review"})
    else:
        requests = list_specific_evidence_requests(conn, ticker=ticker_value, status="open")
        for request in requests:
            evidence_type = str(request.get("evidence_type") or "")
            context = _route_context(conn, ticker_value, evidence_type)
            items.append(
                {
                    "followup_item_id": followup_item_id_for(ticker_value, evidence_type),
                    "ticker": ticker_value,
                    "source_request_id": request.get("request_id"),
                    "item_type": ITEM_TYPE_BY_EVIDENCE_TYPE.get(evidence_type, "SPECIFIC_EVIDENCE_REQUEST"),
                    "evidence_type": evidence_type,
                    "priority": request.get("priority"),
                    "status": request.get("status"),
                    "route_status": context.get("status"),
                    "allowed_usage_target": request.get("allowed_usage") or ALLOWED_USAGE_BY_EVIDENCE_TYPE.get(evidence_type),
                    "availability_judgment": request.get("availability_judgment"),
                    "feasibility": request.get("feasibility"),
                    "expected_output": request.get("expected_output"),
                    "do_not_do": request.get("do_not_do") or context.get("do_not_do") or [],
                    "pending_created": False,
                    "paper_order_created": False,
                    "promotion_allowed": False,
                }
            )
    by_type = Counter(item.get("evidence_type") for item in items)
    manual_research_required = sum(
        1
        for item in items
        if item.get("evidence_type") in {"supplier_share", "confirmed_customer_allocation"}
        or item.get("feasibility") == "manual_research_required"
    )
    return {
        "generated_at": now_ts(),
        "summary": {
            "followup_queue_items": len(items),
            "official_consensus_requests": by_type.get("official_consensus", 0),
            "supplier_share_requests": by_type.get("supplier_share", 0),
            "customer_allocation_requests": by_type.get("confirmed_customer_allocation", 0),
            "manual_research_required": manual_research_required,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed_true": 0,
        },
        "items": sorted(items, key=lambda row: (str(row.get("priority")), str(row.get("evidence_type")))),
        "excluded_rows": excluded_rows,
        "safety": {
            "evidence_written": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }
