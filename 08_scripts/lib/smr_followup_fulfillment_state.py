#!/usr/bin/env python3
"""Phase 42 follow-up request fulfillment state.

This module reads Phase 41 specific evidence requests and classifies how each
request can be fulfilled. It does not write evidence, pending review, paper
orders, or promotion state.
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from typing import Any

from smr_customer_allocation_route import build_customer_allocation_route
from smr_official_consensus_availability import build_official_consensus_availability
from smr_research_followup_queue import CORE_EVIDENCE_TYPES
from smr_research_review_lifecycle import REPAIR_ONLY_TICKER, TARGET_REVIEW_TICKER, normalize_ticker
from smr_specific_evidence_request import get_specific_evidence_request, evidence_request_id_for
from smr_supplier_share_route import build_supplier_share_route
from smr_wiki import now_ts


FULFILLMENT_STATUSES = {
    "open",
    "fulfilled",
    "partial_fulfilled",
    "manual_input_required",
    "authorized_source_required",
    "scenario_only",
    "proxy_only",
    "blocked",
    "not_publicly_confirmable",
    "rejected",
    "unknown",
}


def _request_or_placeholder(conn: sqlite3.Connection, ticker: str, evidence_type: str) -> dict[str, Any]:
    request = get_specific_evidence_request(conn, evidence_request_id_for(ticker, evidence_type))
    if request:
        return request
    return {
        "request_id": evidence_request_id_for(ticker, evidence_type),
        "ticker": ticker,
        "evidence_type": evidence_type,
        "status": "missing_request",
        "allowed_usage": None,
        "do_not_do": [],
    }


def _row_for(conn: sqlite3.Connection, ticker: str, request: dict[str, Any]) -> dict[str, Any]:
    evidence_type = str(request.get("evidence_type") or "")
    if evidence_type == "official_consensus":
        body = build_official_consensus_availability(conn, ticker).get("official_consensus_availability") or {}
        return {
            "request_type": evidence_type,
            "request_id": request.get("request_id"),
            "request_status": request.get("status"),
            "status": "authorized_source_required",
            "current_evidence_status": "not_available",
            "allowed_usage": "none_until_authorized_source",
            "next_action": "provide_authorized_consensus_source_metadata",
            "specific_request_open": bool(body.get("specific_request_open")),
            "can_be_confirmed": False,
            "do_not_do": body.get("do_not_do") or request.get("do_not_do") or [],
        }
    if evidence_type == "supplier_share":
        body = build_supplier_share_route(conn, ticker).get("supplier_share_route") or {}
        return {
            "request_type": evidence_type,
            "request_id": request.get("request_id"),
            "request_status": request.get("status"),
            "status": "scenario_only",
            "current_evidence_status": "not_publicly_confirmable",
            "allowed_usage": "scenario_analysis_only",
            "next_action": "create_explicit_scenario_assumption_if_needed",
            "specific_request_open": bool(body.get("specific_request_open")),
            "can_be_confirmed": False,
            "do_not_do": body.get("do_not_do") or request.get("do_not_do") or [],
        }
    if evidence_type == "confirmed_customer_allocation":
        body = build_customer_allocation_route(conn, ticker).get("customer_allocation_route") or {}
        return {
            "request_type": evidence_type,
            "request_id": request.get("request_id"),
            "request_status": request.get("status"),
            "status": "proxy_only",
            "current_evidence_status": "proxy_available_not_confirmed",
            "allowed_usage": "bear_case_context_or_scenario_support",
            "next_action": "search for direct disclosure or customer-side public statement",
            "specific_request_open": bool(body.get("specific_request_open")),
            "can_be_confirmed": False,
            "do_not_do": body.get("do_not_do") or request.get("do_not_do") or [],
        }
    return {
        "request_type": evidence_type or "unknown",
        "request_id": request.get("request_id"),
        "request_status": request.get("status"),
        "status": "unknown",
        "current_evidence_status": "unknown",
        "allowed_usage": "blocked",
        "next_action": "manual_review_required",
        "specific_request_open": False,
        "can_be_confirmed": False,
        "do_not_do": request.get("do_not_do") or [],
    }


def build_followup_fulfillment_state(
    conn: sqlite3.Connection,
    ticker: str = TARGET_REVIEW_TICKER,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    if ticker == REPAIR_ONLY_TICKER:
        return {
            "generated_at": now_ts(),
            "ticker": ticker,
            "followup_fulfillment_state": {
                "requests_total": 0,
                "fulfilled": 0,
                "partial_fulfilled": 0,
                "manual_input_required": 0,
                "authorized_source_required": 0,
                "scenario_only": 0,
                "proxy_only": 0,
                "request_rows": [],
                "excluded_reason": "repair_required_before_review",
            },
            "safety": {
                "evidence_written": False,
                "pending_created": 0,
                "paper_order_created": 0,
                "promotion_rules_relaxed": False,
            },
        }
    rows = [
        _row_for(conn, ticker, _request_or_placeholder(conn, ticker, evidence_type))
        for evidence_type in CORE_EVIDENCE_TYPES
    ]
    counts = Counter(row.get("status") for row in rows)
    body = {
        "requests_total": len(rows),
        "fulfilled": counts.get("fulfilled", 0),
        "partial_fulfilled": counts.get("partial_fulfilled", 0),
        "manual_input_required": 1,
        "authorized_source_required": counts.get("authorized_source_required", 0),
        "scenario_only": counts.get("scenario_only", 0),
        "proxy_only": counts.get("proxy_only", 0),
        "request_rows": rows,
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "followup_fulfillment_state": body,
        "safety": {
            "request_is_evidence": False,
            "confirmed_variable_added": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }
