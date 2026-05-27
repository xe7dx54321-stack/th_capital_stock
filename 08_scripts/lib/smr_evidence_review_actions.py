#!/usr/bin/env python3
"""Manual evidence review actions with Phase 31 safety guards."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_download_repair_queue import upsert_download_repair_task
from smr_evidence_lifecycle import (
    DEFAULT_ALLOWED_USAGE,
    downgrade_allowed_usage,
    get_lifecycle_state,
    lifecycle_from_candidate,
    load_semantic_evidence_candidate,
    upsert_lifecycle_state,
    validate_status_transition,
)
from smr_evidence_review_audit import write_evidence_review_audit
from smr_sensitive_variable_guard import FORBIDDEN_CONFIRMED_UPGRADES, guard_sensitive_variable
from smr_wiki import now_ts


ALLOWED_ACTIONS = {
    "approve_evidence",
    "reject_evidence",
    "downgrade_usage",
    "mark_as_noise",
    "request_better_source",
    "link_to_variable_pack",
    "archive_evidence",
}

FORBIDDEN_ACTIONS = set(FORBIDDEN_CONFIRMED_UPGRADES)


ACTION_TO_STATUS = {
    "approve_evidence": "approved_evidence",
    "reject_evidence": "rejected_evidence",
    "downgrade_usage": "downgraded_evidence",
    "mark_as_noise": "marked_noise",
    "request_better_source": "needs_better_source",
    "link_to_variable_pack": "linked_to_variable_pack",
    "archive_evidence": "archived",
}

ACTION_TO_REVIEW_STATUS = {
    "approve_evidence": "reviewed",
    "reject_evidence": "reviewed",
    "downgrade_usage": "reviewed",
    "mark_as_noise": "reviewed",
    "request_better_source": "needs_follow_up",
    "link_to_variable_pack": "reviewed",
    "archive_evidence": "reviewed",
}


def _safe_before_state(conn: sqlite3.Connection, evidence_id: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    state = get_lifecycle_state(conn, evidence_id)
    candidate = load_semantic_evidence_candidate(conn, evidence_id)
    if not state and candidate:
        state = lifecycle_from_candidate(candidate)
    if not state:
        raise ValueError(f"evidence not found: {evidence_id}")
    return state, candidate


def _after_state(
    before: dict[str, Any],
    *,
    action: str,
    target_usage: str | None,
    reason: str | None,
    candidate: dict[str, Any] | None,
) -> dict[str, Any]:
    after = dict(before)
    after["lifecycle_status"] = ACTION_TO_STATUS[action]
    after["review_status"] = ACTION_TO_REVIEW_STATUS[action]
    after["last_reviewed_at"] = now_ts()
    after["usable_for_promotion"] = False
    metadata = dict(after.get("metadata") or {})
    metadata.update(
        {
            "last_review_action": action,
            "last_review_reason": reason,
            "approved_is_not_promotion": True,
            "paper_order_allowed": False,
            "pending_allowed": False,
        }
    )
    after["metadata"] = metadata
    if action == "downgrade_usage":
        after["allowed_usage"] = target_usage or "context_only"
    elif action == "mark_as_noise":
        after["allowed_usage"] = "blocked"
        after["review_status"] = "blocked"
    elif action == "request_better_source":
        after["allowed_usage"] = min_usage(before.get("allowed_usage"), "context_only")
    elif action == "approve_evidence":
        after["allowed_usage"] = before.get("allowed_usage") or DEFAULT_ALLOWED_USAGE
    elif action == "link_to_variable_pack":
        after["allowed_usage"] = before.get("allowed_usage") or DEFAULT_ALLOWED_USAGE
        metadata["link_to_variable_pack_requires_gate"] = True
    if candidate:
        guard = guard_sensitive_variable({**candidate, "evidence_status": candidate.get("evidence_status"), "allowed_usage": after.get("allowed_usage")}, action=action)
        if guard.get("is_sensitive") and after.get("allowed_usage") not in {"scenario_analysis_only", "context_only", "blocked", "planned_only"}:
            after["allowed_usage"] = "scenario_analysis_only"
        metadata["sensitive_guard"] = guard
    return after


def min_usage(left: str | None, right: str) -> str:
    ok, _ = downgrade_allowed_usage(left, right)
    return right if ok else (left or right)


def validate_review_action(
    before: dict[str, Any],
    *,
    action: str,
    target_usage: str | None = None,
    candidate: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if action in FORBIDDEN_ACTIONS:
        return False, [f"forbidden action blocked: {action}"]
    if action not in ALLOWED_ACTIONS:
        return False, [f"unsupported action: {action}"]
    if action == "downgrade_usage":
        ok, reason = downgrade_allowed_usage(before.get("allowed_usage"), target_usage or "context_only")
        if not ok:
            reasons.append(reason)
    if action == "mark_as_noise" and before.get("lifecycle_status") == "archived":
        reasons.append("archived evidence cannot be marked noise")
    after_status = ACTION_TO_STATUS.get(action)
    ok, reason = validate_status_transition(before.get("lifecycle_status"), str(after_status))
    if not ok:
        reasons.append(reason)
    guard = guard_sensitive_variable(candidate or before, action=action)
    if action in FORBIDDEN_ACTIONS or any("cannot confirm" in str(v) for v in guard.get("violations") or []):
        reasons.extend(guard.get("violations") or [])
    return not reasons, reasons or ["allowed"]


def apply_evidence_review_action(
    conn: sqlite3.Connection,
    *,
    evidence_id: str,
    action: str,
    reason: str | None = None,
    target_usage: str | None = None,
    actor: str = "human_or_system",
    dry_run: bool = True,
) -> dict[str, Any]:
    before, candidate = _safe_before_state(conn, evidence_id)
    allowed, reasons = validate_review_action(before, action=action, target_usage=target_usage, candidate=candidate)
    if not allowed:
        return {
            "evidence_id": evidence_id,
            "action": action,
            "mode": "dry_run" if dry_run else "execute",
            "allowed": False,
            "reason": "; ".join(reasons),
            "before": {
                "lifecycle_status": before.get("lifecycle_status"),
                "allowed_usage": before.get("allowed_usage"),
                "usable_for_promotion": False,
            },
            "after": {
                "lifecycle_status": before.get("lifecycle_status"),
                "allowed_usage": before.get("allowed_usage"),
                "usable_for_promotion": False,
            },
            "safety_checks": safety_checks(),
            "would_write_audit_log": False,
        }
    after = _after_state(before, action=action, target_usage=target_usage, reason=reason, candidate=candidate)
    result = {
        "evidence_id": evidence_id,
        "action": action,
        "mode": "dry_run" if dry_run else "execute",
        "allowed": True,
        "reason": reason or "review action accepted by Phase 31 guard",
        "before": {
            "lifecycle_status": before.get("lifecycle_status"),
            "allowed_usage": before.get("allowed_usage"),
            "usable_for_promotion": False,
        },
        "after": {
            "lifecycle_status": after.get("lifecycle_status"),
            "allowed_usage": after.get("allowed_usage"),
            "usable_for_promotion": False,
        },
        "safety_checks": safety_checks(),
        "would_write_audit_log": True,
    }
    if dry_run:
        return result
    stored = upsert_lifecycle_state(conn, after)
    audit = write_evidence_review_audit(
        conn,
        evidence_id=evidence_id,
        ticker=stored.get("ticker"),
        action=action,
        actor=actor,
        mode="execute",
        before=before,
        after=stored,
        reason=reason,
        metadata={"target_usage": target_usage, "candidate_found": bool(candidate)},
    )
    if action == "request_better_source":
        source_id = stored.get("source_id") or evidence_id
        upsert_download_repair_task(
            conn,
            {
                "source_id": source_id,
                "ticker": stored.get("ticker"),
                "source_url": stored.get("source_url"),
                "task_type": "MANUAL_TEXT_NEEDED",
                "priority": "medium",
                "reason": reason or "manual review requested better source",
                "recommended_action": "manual_text_needed",
            },
        )
    result["audit_record"] = audit
    result["stored_lifecycle"] = stored
    return result


def safety_checks() -> dict[str, Any]:
    return {
        "confirmed_variable_upgrade_blocked": True,
        "promotion_allowed": False,
        "paper_order_allowed": False,
        "pending_allowed": False,
        "usable_for_promotion": False,
    }
