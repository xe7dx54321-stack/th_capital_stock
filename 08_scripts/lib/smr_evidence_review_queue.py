#!/usr/bin/env python3
"""Evidence review queue builder for Phase 31 governance."""

from __future__ import annotations

import hashlib
import sqlite3
from collections import Counter
from typing import Any

from smr_download_repair_queue import list_download_repair_tasks
from smr_evidence_lifecycle import (
    list_lifecycle_states,
    list_semantic_evidence_candidates,
)
from smr_phase25_utils import resolve_phase25_tickers
from smr_semantic_evidence_persistence import build_semantic_evidence_candidates, flatten_candidates, guard_semantic_evidence_candidates
from smr_sensitive_variable_guard import guard_sensitive_variable, is_sensitive_variable


SENSITIVE_VARIABLE_TYPES = {
    "supplier_share",
    "supplier_share_signal",
    "ASP_price_proxy",
    "ASP_price_signal",
    "customer_allocation_proxy",
    "customer_allocation_signal",
    "official_consensus",
    "confirmed_order",
}

DEFAULT_ACTIONS = [
    "approve_evidence",
    "reject_evidence",
    "downgrade_usage",
    "mark_as_noise",
    "request_better_source",
]


def review_item_id_for(item_type: str, item_id: str) -> str:
    suffix = hashlib.sha1(f"{item_type}|{item_id}".encode("utf-8")).hexdigest()[:16]
    return f"review_{suffix}"


def _quality(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = candidate.get("payload") or {}
    quality = payload.get("quality") or candidate.get("quality") or {}
    return quality if isinstance(quality, dict) else {}


def _candidate_by_id(conn: sqlite3.Connection, ticker: str | None = None) -> dict[str, dict[str, Any]]:
    return {str(candidate.get("evidence_id")): candidate for candidate in list_semantic_evidence_candidates(conn, ticker=ticker)}


def _review_reason(candidate: dict[str, Any], state: dict[str, Any] | None) -> list[str]:
    quality = _quality(candidate)
    bucket = state.get("quality_bucket") if state else quality.get("quality_bucket")
    reasons = []
    if (state or {}).get("review_status") == "review_required":
        reasons.append("review_required")
    if bucket == "weak_but_usable":
        reasons.append("weak_but_usable")
    if bucket == "review_required":
        reasons.append("review_required_quality_bucket")
    if is_sensitive_variable(candidate.get("variable_type")):
        reasons.append("sensitive_variable_type")
    if (state or {}).get("lifecycle_status") in {"rejected_evidence", "marked_noise", "removed"}:
        reasons.append(str((state or {}).get("lifecycle_status")))
    if not reasons and (candidate.get("usable_for_expectation_gap") or candidate.get("usable_for_valuation_support")):
        reasons.append("variable_pack_impact_uncertain")
    return list(dict.fromkeys(reasons))


def priority_for_review(reasons: list[str], candidate: dict[str, Any]) -> str:
    sensitive = is_sensitive_variable(candidate.get("variable_type"))
    if "review_required" in reasons or "review_required_quality_bucket" in reasons:
        return "high"
    if sensitive and ("weak_but_usable" in reasons or candidate.get("variable_type") in SENSITIVE_VARIABLE_TYPES):
        return "high"
    if "weak_but_usable" in reasons or "variable_pack_impact_uncertain" in reasons:
        return "medium"
    return "low"


def queue_item_from_candidate(candidate: dict[str, Any], state: dict[str, Any] | None = None) -> dict[str, Any] | None:
    reasons = _review_reason(candidate, state)
    if not reasons:
        return None
    quality = _quality(candidate)
    sensitive_guard = guard_sensitive_variable(candidate)
    lifecycle_status = (state or {}).get("lifecycle_status") or "persisted_candidate"
    allowed_actions = list(DEFAULT_ACTIONS)
    if lifecycle_status not in {"marked_noise", "rejected_evidence", "archived", "removed"}:
        allowed_actions.append("link_to_variable_pack")
        allowed_actions.append("archive_evidence")
    return {
        "review_item_id": review_item_id_for("evidence_candidate_review", str(candidate.get("evidence_id"))),
        "item_type": "evidence_candidate_review",
        "ticker": candidate.get("ticker"),
        "evidence_id": candidate.get("evidence_id"),
        "priority": priority_for_review(reasons, candidate),
        "review_reason": reasons,
        "variable_type": candidate.get("variable_type"),
        "quality_score": (state or {}).get("quality_score") or quality.get("quality_score"),
        "quality_bucket": (state or {}).get("quality_bucket") or quality.get("quality_bucket"),
        "quoted_span": candidate.get("quoted_span"),
        "quoted_span_preview": " ".join(str(candidate.get("quoted_span") or "").split())[:220],
        "source_url": candidate.get("source_url"),
        "source_type": candidate.get("source_type"),
        "noise_flags": ((quality.get("noise") or {}).get("noise_types") or []),
        "allowed_usage": (state or {}).get("allowed_usage") or candidate.get("allowed_usage"),
        "recommended_action": "review_before_linking" if sensitive_guard.get("is_sensitive") else "review_candidate",
        "allowed_actions": allowed_actions,
        "lifecycle_status": lifecycle_status,
        "usable_for_promotion": False,
    }


def queue_item_from_repair_task(task: dict[str, Any]) -> dict[str, Any]:
    priority = task.get("priority") or "medium"
    if task.get("task_type") in {"MANUAL_TEXT_NEEDED", "IR_SOURCE_DOWNLOAD_UNAVAILABLE"}:
        priority = "medium"
    return {
        "review_item_id": review_item_id_for("download_repair", str(task.get("repair_task_id"))),
        "item_type": "download_repair",
        "ticker": task.get("ticker"),
        "evidence_id": None,
        "source_id": task.get("source_id"),
        "priority": priority,
        "review_reason": [str(task.get("task_type") or "download_unavailable")],
        "variable_type": None,
        "quality_score": None,
        "quality_bucket": None,
        "quoted_span": None,
        "quoted_span_preview": "",
        "source_url": task.get("source_url"),
        "source_type": "real_ir_source",
        "noise_flags": [],
        "allowed_usage": "blocked",
        "recommended_action": task.get("recommended_action"),
        "allowed_actions": ["request_better_source", "archive_evidence"],
        "repair_task_id": task.get("repair_task_id"),
        "lifecycle_status": "needs_better_source",
        "usable_for_promotion": False,
    }


def build_review_queue(conn: sqlite3.Connection, *, ticker: str | None = None, include_low_priority: bool = True) -> dict[str, Any]:
    states = {state.get("evidence_id"): state for state in list_lifecycle_states(conn, ticker=ticker)}
    candidates = _candidate_by_id(conn, ticker=ticker)
    items: list[dict[str, Any]] = []
    for evidence_id, candidate in candidates.items():
        item = queue_item_from_candidate(candidate, states.get(evidence_id))
        if item and (include_low_priority or item.get("priority") != "low"):
            items.append(item)
    for state in states.values():
        if state.get("evidence_id") in candidates:
            continue
        if state.get("lifecycle_status") not in {"rejected_evidence", "marked_noise", "removed"}:
            continue
        items.append(
            {
                "review_item_id": review_item_id_for("evidence_lifecycle_audit", str(state.get("evidence_id"))),
                "item_type": "evidence_lifecycle_audit",
                "ticker": state.get("ticker"),
                "evidence_id": state.get("evidence_id"),
                "priority": "low",
                "review_reason": [str(state.get("lifecycle_status"))],
                "variable_type": state.get("variable_type"),
                "quality_score": state.get("quality_score"),
                "quality_bucket": state.get("quality_bucket"),
                "quoted_span_preview": state.get("quoted_span_preview"),
                "source_url": state.get("source_url"),
                "allowed_actions": ["archive_evidence", "request_better_source"],
                "lifecycle_status": state.get("lifecycle_status"),
                "usable_for_promotion": False,
            }
        )
    for task in list_download_repair_tasks(conn, ticker=ticker):
        if task.get("status") == "open":
            items.append(queue_item_from_repair_task(task))
    priority_order = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda item: (priority_order.get(str(item.get("priority")), 9), str(item.get("ticker") or ""), str(item.get("review_item_id"))))
    priorities = Counter(item.get("priority") for item in items)
    types = Counter(item.get("item_type") for item in items)
    return {
        "summary": {
            "review_queue_items": len(items),
            "high_priority": priorities.get("high", 0),
            "medium_priority": priorities.get("medium", 0),
            "low_priority": priorities.get("low", 0),
            "evidence_candidate_review": types.get("evidence_candidate_review", 0),
            "download_repair_items": types.get("download_repair", 0),
            "sensitive_variable_items": sum(1 for item in items if is_sensitive_variable(item.get("variable_type"))),
            "promotion_allowed_true": sum(1 for item in items if item.get("usable_for_promotion")),
        },
        "items": items,
    }


def build_generated_review_items(conn: sqlite3.Connection, *, tickers: str | None = None) -> list[dict[str, Any]]:
    """Include Phase 30 candidates that were not persisted because they need review or were rejected."""

    items: list[dict[str, Any]] = []
    for ticker in resolve_phase25_tickers(tickers):
        payload = build_semantic_evidence_candidates(conn, ticker, use_real_sources=True, use_text_cache=True, mode="mock")
        candidates = flatten_candidates(payload)
        guarded = guard_semantic_evidence_candidates(candidates, reject_noisy=True)
        for candidate in guarded.get("review_required_candidates") or []:
            item = queue_item_from_candidate(
                candidate,
                {
                    "lifecycle_status": "pending_review",
                    "review_status": "review_required",
                    "quality_score": (candidate.get("quality") or {}).get("quality_score"),
                    "quality_bucket": (candidate.get("quality") or {}).get("quality_bucket"),
                    "allowed_usage": candidate.get("allowed_usage"),
                },
            )
            if item:
                item["item_type"] = "evidence_candidate_review"
                item["recommended_action"] = "manual_review_required"
                items.append(item)
        for candidate in guarded.get("rejected_candidates") or []:
            quality = candidate.get("quality") or {}
            lifecycle_status = "marked_noise" if ((quality.get("noise") or {}).get("recommended_action") == "reject") else "rejected_evidence"
            item = queue_item_from_candidate(
                candidate,
                {
                    "lifecycle_status": lifecycle_status,
                    "review_status": "blocked",
                    "quality_score": quality.get("quality_score"),
                    "quality_bucket": quality.get("quality_bucket"),
                    "allowed_usage": "blocked",
                },
            )
            if item:
                item["item_type"] = "evidence_candidate_audit"
                item["recommended_action"] = "audit_rejected_candidate"
                items.append(item)
    return items


def build_review_queue_with_generated_candidates(
    conn: sqlite3.Connection,
    *,
    tickers: str | None = None,
    include_low_priority: bool = True,
) -> dict[str, Any]:
    resolved = resolve_phase25_tickers(tickers)
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ticker in resolved:
        payload = build_review_queue(conn, ticker=ticker, include_low_priority=include_low_priority)
        for item in payload.get("items") or []:
            key = str(item.get("review_item_id"))
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    for item in build_generated_review_items(conn, tickers=",".join(resolved)):
        key = str(item.get("review_item_id"))
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    merged.sort(key=lambda item: (priority_order.get(str(item.get("priority")), 9), str(item.get("ticker") or ""), str(item.get("review_item_id"))))
    priorities = Counter(item.get("priority") for item in merged)
    types = Counter(item.get("item_type") for item in merged)
    return {
        "summary": {
            "tickers_checked": len(resolved),
            "review_queue_items": len(merged),
            "high_priority": priorities.get("high", 0),
            "medium_priority": priorities.get("medium", 0),
            "low_priority": priorities.get("low", 0),
            "evidence_candidate_review": types.get("evidence_candidate_review", 0),
            "evidence_candidate_audit": types.get("evidence_candidate_audit", 0),
            "download_repair_items": types.get("download_repair", 0),
            "sensitive_variable_items": sum(1 for item in merged if is_sensitive_variable(item.get("variable_type"))),
            "promotion_allowed_true": sum(1 for item in merged if item.get("usable_for_promotion")),
        },
        "items": merged,
    }
