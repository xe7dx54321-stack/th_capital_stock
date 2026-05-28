#!/usr/bin/env python3
"""Phase 44 manual candidate review action engine."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_manual_candidate_review_audit import write_manual_candidate_review_audit
from smr_manual_candidate_review_lifecycle import (
    STATUS_BY_ACTION,
    canonical_candidate_type,
    lifecycle_from_candidate,
    load_lifecycle,
    load_or_build_candidate,
    upsert_lifecycle,
)
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


VALID_ACTIONS = set(STATUS_BY_ACTION)
FORBIDDEN_ACTIONS = {
    "confirm_official_consensus",
    "confirm_supplier_share",
    "confirm_customer_allocation",
    "allow_promotion",
    "create_pending",
    "create_paper_order",
    "create_position",
    "create_trade",
}


def _validate_action(candidate_type: str, action: str) -> tuple[bool, str]:
    if action in FORBIDDEN_ACTIONS:
        return False, "forbidden_manual_candidate_review_action"
    if action not in VALID_ACTIONS:
        return False, "unsupported_manual_candidate_review_action"
    if candidate_type == "supplier_share" and action == "mark_as_proxy_only":
        return False, "supplier_share_should_be_scenario_only_not_proxy_only"
    if candidate_type == "customer_allocation" and action == "mark_as_scenario_only":
        return False, "customer_allocation_proxy_should_be_proxy_only"
    return True, "allowed"


def apply_manual_candidate_review_action(
    conn: sqlite3.Connection,
    *,
    ticker: str = TARGET_REVIEW_TICKER,
    candidate_type: str = "official_consensus",
    action: str = "accept_as_candidate",
    mode: str = "dry_run",
) -> dict[str, Any]:
    if mode not in {"dry_run", "execute"}:
        raise ValueError(f"Unsupported mode: {mode}")
    ticker = normalize_ticker(ticker)
    canonical = canonical_candidate_type(candidate_type)
    allowed, reason = _validate_action(canonical, action)
    if not allowed:
        return {
            "generated_at": now_ts(),
            "ticker": ticker,
            "manual_candidate_review_action": {
                "candidate_type": canonical,
                "action": action,
                "mode": mode,
                "action_allowed": False,
                "blocked_reason": reason,
                "audit_written": False,
                "usable_for_promotion": False,
                "pending_created": False,
                "paper_order_created": False,
            },
            "safety": {
                "forbidden_action_intercepted": action in FORBIDDEN_ACTIONS,
                "candidate_confirmed": False,
                "pending_created": 0,
                "paper_order_created": 0,
                "promotion_rules_relaxed": False,
                "real_trade_risk": False,
            },
        }

    candidate = load_or_build_candidate(conn, ticker=ticker, candidate_type=canonical, materialize=mode == "execute")
    existing = load_lifecycle(conn, str(candidate.get("candidate_id")))
    before_status = (existing or {}).get("status") or "manual_candidate_created"
    after_status = STATUS_BY_ACTION[action]
    lifecycle = lifecycle_from_candidate(candidate, status=after_status, action=action)
    lifecycle["before_status"] = before_status
    audit_record: dict[str, Any] = {}
    audit_written = False
    if mode == "execute":
        updated = upsert_lifecycle(conn, lifecycle)
        before_status = updated.get("before_status") or before_status
        after_status = updated.get("after_status") or after_status
        audit_record = write_manual_candidate_review_audit(
            conn,
            ticker=ticker,
            candidate_id=str(candidate.get("candidate_id")),
            candidate_type=canonical,
            action=action,
            before_status=before_status,
            after_status=after_status,
            confirmation_status_after_action=str(lifecycle.get("confirmation_status")),
            allowed_usage_after_action=str(lifecycle.get("allowed_usage")),
            metadata={
                "accepted_is_not_confirmed": True,
                "review_action_connected_to_promotion_gate": False,
                "manual_intake_branch_closeout": True,
            },
        )
        audit_written = True

    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "manual_candidate_review_action": {
            "candidate_type": canonical,
            "candidate_id": candidate.get("candidate_id"),
            "action": action,
            "mode": mode,
            "action_allowed": True,
            "before_status": before_status,
            "after_status": after_status,
            "confirmation_status": lifecycle.get("confirmation_status"),
            "allowed_usage_after_action": lifecycle.get("allowed_usage"),
            "audit_written": audit_written,
            "audit_record": audit_record,
            "usable_for_promotion": False,
            "pending_created": False,
            "paper_order_created": False,
        },
        "safety": {
            "accept_as_candidate_is_confirmed": False,
            "scenario_only_is_fact": False,
            "proxy_only_is_confirmed_allocation": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }
