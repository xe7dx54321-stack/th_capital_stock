#!/usr/bin/env python3
"""Phase 40 research review queue builder."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_evidence_contribution_analyzer import build_evidence_contribution
from smr_research_evidence_chain import build_research_evidence_chain
from smr_research_review_actions import ALLOWED_REVIEW_ACTIONS
from smr_research_review_candidate import build_research_review_candidate_decision
from smr_research_review_lifecycle import (
    DEFAULT_COMPANY_NAMES,
    REPAIR_ONLY_TICKER,
    TARGET_REVIEW_TICKER,
    build_phase39_lifecycle_object,
    get_lifecycle_by_ticker,
    normalize_ticker,
)
from smr_wiki import now_ts


WHY_NOT_PENDING_CODES = [
    "supplier_share_unconfirmed",
    "official_consensus_missing",
    "confirmed_customer_allocation_missing",
]


def _evidence_after(conn: sqlite3.Connection, ticker: str) -> int:
    chain = build_research_evidence_chain(conn, ticker).get("evidence_chain") or {}
    return int(chain.get("total_evidence") or 0)


def _queue_item_for_300308(conn: sqlite3.Connection) -> dict[str, Any] | None:
    ticker = TARGET_REVIEW_TICKER
    decision_payload = build_research_review_candidate_decision(conn, ticker)
    decision = decision_payload.get("research_review_decision") or {}
    boundary = decision.get("promotion_boundary") or {}
    contribution = build_evidence_contribution(conn, ticker).get("evidence_contribution") or {}
    variables = contribution.get("variables_strengthened") or []
    total_evidence = _evidence_after(conn, ticker)
    checklist_present = bool(decision.get("human_review_questions"))
    why_not_pending = decision.get("why_not_pending") or []
    no_sensitive_violation = not (decision_payload.get("safety") or {}).get("sensitive_guard_violation")
    eligible = (
        decision.get("decision") == "research_review_candidate"
        and boundary.get("pending_allowed") is False
        and boundary.get("paper_order_allowed") is False
        and total_evidence > 0
        and bool(why_not_pending)
        and checklist_present
        and no_sensitive_violation
    )
    if not eligible:
        return None
    lifecycle = get_lifecycle_by_ticker(conn, ticker) or build_phase39_lifecycle_object(conn, ticker)
    return {
        "review_candidate_id": lifecycle.get("review_candidate_id"),
        "ticker": ticker,
        "company_name": DEFAULT_COMPANY_NAMES.get(ticker),
        "status": lifecycle.get("research_review_status"),
        "review_action_status": lifecycle.get("review_action_status"),
        "confidence": decision.get("confidence"),
        "evidence_after": total_evidence,
        "strengthened_variables": variables,
        "why_not_pending": [
            "supplier_share_unconfirmed",
            "official_consensus_missing",
            "confirmed_customer_allocation_missing",
        ],
        "recommended_review_action": "request_deeper_research",
        "allowed_actions": list(ALLOWED_REVIEW_ACTIONS),
        "pending_allowed": False,
        "paper_order_allowed": False,
        "promotion_allowed": False,
    }


def _repair_row_for_300394() -> dict[str, Any]:
    return {
        "ticker": REPAIR_ONLY_TICKER,
        "company_name": DEFAULT_COMPANY_NAMES.get(REPAIR_ONLY_TICKER),
        "status": "repair_required_before_review",
        "recommended_action": "repair_evidence_chain",
        "why_not_queue": [
            "repair_required_before_research_deepening",
            "evidence_chain_count remains 0",
        ],
        "pending_allowed": False,
        "paper_order_allowed": False,
        "promotion_allowed": False,
    }


def build_research_review_queue(conn: sqlite3.Connection, ticker: str | None = None) -> dict[str, Any]:
    ticker_filter = normalize_ticker(ticker) if ticker else None
    items: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    if ticker_filter in (None, TARGET_REVIEW_TICKER):
        item = _queue_item_for_300308(conn)
        if item:
            items.append(item)
    if ticker_filter in (None, REPAIR_ONLY_TICKER):
        repair_rows.append(_repair_row_for_300394())
    pending_allowed_true = sum(1 for item in [*items, *repair_rows] if item.get("pending_allowed"))
    paper_order_allowed_true = sum(1 for item in [*items, *repair_rows] if item.get("paper_order_allowed"))
    return {
        "generated_at": now_ts(),
        "summary": {
            "queue_items": len(items),
            "research_review_candidates": sum(1 for item in items if item.get("status") == "research_review_candidate"),
            "repair_required": len(repair_rows),
            "pending_allowed_true": pending_allowed_true,
            "paper_order_allowed_true": paper_order_allowed_true,
            "promotion_allowed_true": sum(1 for item in [*items, *repair_rows] if item.get("promotion_allowed")),
        },
        "items": items,
        "repair_rows": repair_rows,
        "safety": {
            "research_review_candidate_is_pending": False,
            "paper_order_allowed_true": paper_order_allowed_true,
            "pending_allowed_true": pending_allowed_true,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }
