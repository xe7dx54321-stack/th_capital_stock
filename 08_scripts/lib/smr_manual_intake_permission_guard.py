#!/usr/bin/env python3
"""Permission and allowed-usage guard for Phase 43 manual candidates."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_manual_intake_candidate_generator import (
    FINAL_ALLOWED_USAGE,
    build_candidate_generation_payload,
    list_manual_intake_candidates,
)
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


EQUIVALENT_ALLOWED_USAGE = {
    ("expectation_gap_benchmark", "expectation_gap_benchmark_if_authorized"),
}


def _is_equivalent_requested_usage(requested: str | None, final: str | None) -> bool:
    if requested == final:
        return True
    return (str(requested or ""), str(final or "")) in EQUIVALENT_ALLOWED_USAGE


def _calibrate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    evidence_type = str(candidate.get("evidence_type") or "")
    source_type = str(candidate.get("source_type") or "")
    permission = str(candidate.get("permission_status") or "")
    requested = str(candidate.get("requested_allowed_usage") or "")
    blocked_reasons: list[str] = []
    downgrade_reason = ""
    final_allowed = FINAL_ALLOWED_USAGE.get(evidence_type, candidate.get("allowed_usage") or "blocked")

    if permission in {"unauthorized", "internal_only", "restricted_without_permission"}:
        blocked_reasons.append("permission_status_blocked")
        final_allowed = "blocked"
    if evidence_type == "official_consensus" and permission != "authorized_or_user_provided":
        blocked_reasons.append("official_consensus_requires_authorized_metadata")
        final_allowed = "blocked"
    if evidence_type == "supplier_share" and source_type == "scenario_assumption":
        final_allowed = "scenario_analysis_only"
        if not _is_equivalent_requested_usage(requested, final_allowed):
            downgrade_reason = "supplier share scenario cannot be supporting fact"
    if evidence_type == "confirmed_customer_allocation" and source_type == "proxy_evidence_note":
        final_allowed = "bear_case_context_or_scenario_support"
        if not _is_equivalent_requested_usage(requested, final_allowed):
            downgrade_reason = "customer allocation proxy cannot be confirmed or supporting fact"

    permission_passed = not blocked_reasons
    downgraded = permission_passed and bool(downgrade_reason) and not _is_equivalent_requested_usage(requested, final_allowed)
    return {
        "candidate_id": candidate.get("candidate_id"),
        "ticker": candidate.get("ticker"),
        "evidence_type": evidence_type,
        "source_type": source_type,
        "permission_status": permission,
        "permission_passed": permission_passed,
        "requested_allowed_usage": requested,
        "final_allowed_usage": final_allowed,
        "allowed_usage_downgraded": bool(downgraded),
        "downgrade_reason": downgrade_reason if downgraded else "",
        "blocked_reasons": blocked_reasons,
        "usable_for_promotion": False,
        "pending_created": False,
        "paper_order_created": False,
    }


def candidates_for_permission_audit(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> list[dict[str, Any]]:
    ticker = normalize_ticker(ticker)
    rows = list_manual_intake_candidates(conn, ticker=ticker)
    if rows:
        return rows
    generated = build_candidate_generation_payload(None, ticker=ticker, mode="dry_run")
    return (generated.get("manual_intake_candidate_generation") or {}).get("candidate_rows") or []


def build_permission_audit(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    candidates = candidates_for_permission_audit(conn, ticker)
    audit_rows = [_calibrate_candidate(candidate) for candidate in candidates]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "permission_audit": {
            "manual_candidates_checked": len(audit_rows),
            "permission_passed": sum(1 for row in audit_rows if row.get("permission_passed")),
            "permission_blocked": sum(1 for row in audit_rows if not row.get("permission_passed")),
            "allowed_usage_downgraded": sum(1 for row in audit_rows if row.get("allowed_usage_downgraded")),
            "promotion_allowed_true": 0,
            "audit_rows": audit_rows,
        },
        "safety": {
            "unauthorized_input_blocked": all(row.get("permission_passed") for row in audit_rows)
            or any(row.get("blocked_reasons") for row in audit_rows),
            "usable_for_promotion_true": 0,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }
