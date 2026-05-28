#!/usr/bin/env python3
"""Research-only actions for the Phase 40 workbench."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_research_review_audit import write_audit_record
from smr_research_review_lifecycle import (
    TARGET_REVIEW_TICKER,
    build_phase39_lifecycle_object,
    get_lifecycle_by_ticker,
    normalize_ticker,
    set_lifecycle_status,
    upsert_lifecycle,
    validate_status_transition,
)
from smr_specific_evidence_request import upsert_specific_evidence_request
from smr_wiki import now_ts


ALLOWED_REVIEW_ACTIONS = [
    "continue_evidence_acquisition",
    "request_deeper_research",
    "request_specific_evidence",
    "mark_reviewed",
    "deprioritize",
    "archive_review_candidate",
]

FORBIDDEN_REVIEW_ACTIONS = {
    "approve_pending",
    "approve_paper",
    "create_order",
    "create_position",
    "promote_to_investment_candidate",
    "confirm_supplier_share",
    "confirm_customer_allocation",
    "confirm_official_consensus",
}

ACTION_TRANSITIONS = {
    "continue_evidence_acquisition": ("reviewed_continue_evidence", "needs_follow_up"),
    "request_deeper_research": ("reviewed_request_deeper_research", "needs_follow_up"),
    "request_specific_evidence": ("reviewed_request_specific_evidence", "needs_follow_up"),
    "mark_reviewed": ("reviewed_no_action", "reviewed"),
    "deprioritize": ("reviewed_deprioritize", "reviewed"),
    "archive_review_candidate": ("reviewed_archive", "archived"),
}


def validate_review_action(action: str) -> None:
    if action in FORBIDDEN_REVIEW_ACTIONS:
        raise ValueError(f"Forbidden research-review action: {action}")
    if action not in ALLOWED_REVIEW_ACTIONS:
        raise ValueError(f"Unsupported research-review action: {action}")


def _reason_for(action: str, evidence_type: str | None = None) -> str:
    if action == "request_deeper_research":
        return "Research packet strengthened but key variables remain missing."
    if action == "continue_evidence_acquisition":
        return "Continue research-only evidence acquisition without promotion."
    if action == "request_specific_evidence":
        return f"Request specific evidence for {evidence_type or 'official_consensus'}."
    if action == "mark_reviewed":
        return "Mark research review as reviewed without approving investment pending."
    if action == "deprioritize":
        return "Deprioritize research review candidate while preserving the packet and audit trail."
    if action == "archive_review_candidate":
        return "Archive research review candidate while preserving audit history."
    return "Research review action."


def _current_or_initial_lifecycle(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    current = get_lifecycle_by_ticker(conn, ticker)
    if current:
        return current
    return build_phase39_lifecycle_object(conn, ticker)


def apply_research_review_action(
    conn: sqlite3.Connection,
    *,
    ticker: str = TARGET_REVIEW_TICKER,
    action: str,
    evidence_type: str | None = None,
    mode: str = "dry_run",
    actor: str = "human_or_system",
    reason: str | None = None,
) -> dict[str, Any]:
    validate_review_action(action)
    if mode not in {"dry_run", "execute"}:
        raise ValueError(f"Unsupported mode: {mode}")
    ticker = normalize_ticker(ticker)
    if action == "request_specific_evidence" and not evidence_type:
        evidence_type = "official_consensus"

    lifecycle = _current_or_initial_lifecycle(conn, ticker)
    before_status = str(lifecycle.get("research_review_status") or "unknown")
    after_status, review_action_status = ACTION_TRANSITIONS[action]
    validate_status_transition(before_status, after_status)
    review_candidate_id = str(lifecycle.get("review_candidate_id"))
    action_reason = reason or _reason_for(action, evidence_type)
    creates_follow_up = action in {
        "continue_evidence_acquisition",
        "request_deeper_research",
        "request_specific_evidence",
    }
    specific_request: dict[str, Any] | None = None
    audit: dict[str, Any] | None = None

    if mode == "execute":
        upsert_lifecycle(conn, lifecycle)
        updated = set_lifecycle_status(
            conn,
            review_candidate_id=review_candidate_id,
            research_review_status=after_status,
            review_action_status=review_action_status,
            metadata_updates={
                "last_action": action,
                "last_action_at": now_ts(),
                "last_action_reason": action_reason,
                "follow_up_task_created": creates_follow_up,
                "specific_evidence_type": evidence_type,
                "pending_created": False,
                "paper_order_created": False,
                "promotion_allowed": False,
            },
        )
        if action == "request_specific_evidence":
            specific_request = upsert_specific_evidence_request(
                conn,
                ticker=ticker,
                evidence_type=str(evidence_type),
                review_candidate_id=review_candidate_id,
                source_action=action,
            )
        audit = write_audit_record(
            conn,
            ticker=ticker,
            review_candidate_id=review_candidate_id,
            action=action,
            actor=actor,
            mode="execute",
            before_status=before_status,
            after_status=after_status,
            reason=action_reason,
            metadata={
                "review_action_status": review_action_status,
                "specific_evidence_type": evidence_type,
                "specific_evidence_request_id": (specific_request or {}).get("request_id"),
                "lifecycle_updated_at": updated.get("updated_at"),
            },
        )

    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "action_result": {
            "action": action,
            "evidence_type": evidence_type,
            "mode": mode,
            "before_status": before_status,
            "after_status": after_status,
            "review_action_status_after": review_action_status,
            "would_write_audit": True,
            "audit_written": audit is not None,
            "audit_id": (audit or {}).get("audit_id"),
            "would_create_follow_up_task": creates_follow_up,
            "follow_up_task_created": creates_follow_up if mode == "execute" else False,
            "would_create_specific_evidence_request": action == "request_specific_evidence",
            "specific_evidence_request_created": specific_request is not None,
            "specific_evidence_request_id": (specific_request or {}).get("request_id"),
            "promotion_allowed_after_action": False,
            "pending_created": False,
            "paper_order_created": False,
            "real_trade_triggered": False,
            "forbidden_action_violation": False,
            "reason": action_reason,
        },
        "safety": {
            "research_action_only": True,
            "pending_human_review_created": False,
            "paper_order_created": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }
