#!/usr/bin/env python3
"""Phase 32 read-only evidence review workbench data model."""

from __future__ import annotations

import hashlib
import sqlite3
from collections import Counter
from typing import Any

from smr_evidence_action_command_generator import attach_action_command, action_parameters_for_item, recommended_action_for_item
from smr_evidence_lifecycle import list_lifecycle_states, list_semantic_evidence_candidates
from smr_evidence_review_actions import apply_evidence_review_action
from smr_evidence_review_queue import build_review_queue, build_review_queue_with_generated_candidates
from smr_phase25_utils import resolve_phase25_tickers
from smr_sensitive_variable_guard import FORBIDDEN_CONFIRMED_UPGRADES, guard_sensitive_variable, is_sensitive_variable
from smr_supply_chain_variable_evidence import SEMANTIC_VARIABLE_MAP


COMPANY_NAMES = {
    "300394.SZ": "TFC Communication",
    "300308.SZ": "Zhongji Innolight",
    "688041.SH": "Hygon Information",
    "002230.SZ": "iFLYTEK",
}

SENSITIVE_BLOCKED_ACTIONS = sorted(
    set(FORBIDDEN_CONFIRMED_UPGRADES)
    | {
        "upgrade_to_confirmed_customer_allocation",
        "upgrade_to_confirmed_supplier_share",
        "upgrade_to_confirmed_ASP",
        "upgrade_to_official_consensus",
        "allow_promotion",
    }
)

REVIEWED_LIFECYCLE_STATUSES = {
    "approved_evidence",
    "rejected_evidence",
    "downgraded_evidence",
    "marked_noise",
    "needs_better_source",
    "archived",
    "removed",
}


def _preview(text: Any, limit: int = 220) -> str:
    compact = " ".join(str(text or "").split())
    return compact[:limit]


def _workbench_id(queue_item: dict[str, Any]) -> str:
    raw = str(queue_item.get("evidence_id") or queue_item.get("repair_task_id") or queue_item.get("review_item_id") or "")
    suffix = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    if queue_item.get("evidence_id"):
        return f"wb_{queue_item.get('evidence_id')}"
    return f"wb_{suffix}"


def _candidate_maps(conn: sqlite3.Connection) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    candidates = {str(row.get("evidence_id")): row for row in list_semantic_evidence_candidates(conn)}
    states = {str(row.get("evidence_id")): row for row in list_lifecycle_states(conn)}
    return candidates, states


def _review_status(queue_item: dict[str, Any], state: dict[str, Any] | None) -> str:
    if state and state.get("review_status"):
        return str(state.get("review_status"))
    reasons = set(queue_item.get("review_reason") or [])
    if queue_item.get("lifecycle_status") == "pending_review" or "review_required" in reasons or "review_required_quality_bucket" in reasons:
        return "review_required"
    if queue_item.get("lifecycle_status") in {"rejected_evidence", "marked_noise", "removed"}:
        return "blocked"
    return "not_required"


def _link_status(variable_pack: str | None, sensitive: bool, lifecycle_status: str) -> str:
    if lifecycle_status in {"marked_noise", "rejected_evidence", "removed"}:
        return "blocked"
    if sensitive and variable_pack:
        return "requires_review"
    if variable_pack:
        return "valid"
    return "unlinked"


def normalize_workbench_item(
    queue_item: dict[str, Any],
    *,
    candidate: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    variable_type = queue_item.get("variable_type") or (candidate or {}).get("variable_type") or (state or {}).get("variable_type")
    sensitive = is_sensitive_variable(variable_type)
    lifecycle_status = str(queue_item.get("lifecycle_status") or (state or {}).get("lifecycle_status") or "persisted_candidate")
    review_status = _review_status(queue_item, state)
    variable_pack = SEMANTIC_VARIABLE_MAP.get(str(variable_type or ""))
    link_status = _link_status(variable_pack, sensitive, lifecycle_status)
    source_url = queue_item.get("source_url") or (candidate or {}).get("source_url") or (state or {}).get("source_url")
    quoted_span = queue_item.get("quoted_span") or (candidate or {}).get("quoted_span") or (state or {}).get("quoted_span")
    limitations = queue_item.get("limitations") or (candidate or {}).get("limitations") or (state or {}).get("limitations") or []
    if not isinstance(limitations, list):
        limitations = [limitations]
    item_type = "download_repair" if queue_item.get("item_type") == "download_repair" else "evidence_review"
    if str(queue_item.get("item_type") or "").endswith("_audit"):
        item_type = "evidence_audit"
    guard = guard_sensitive_variable(
        {
            **(candidate or {}),
            "evidence_id": queue_item.get("evidence_id") or (candidate or {}).get("evidence_id"),
            "ticker": queue_item.get("ticker") or (candidate or {}).get("ticker") or (state or {}).get("ticker"),
            "variable_type": variable_type,
            "allowed_usage": queue_item.get("allowed_usage") or (state or {}).get("allowed_usage") or (candidate or {}).get("allowed_usage"),
            "usable_for_promotion": False,
        }
    )
    normalized = {
        "workbench_item_id": _workbench_id(queue_item),
        "review_item_id": queue_item.get("review_item_id"),
        "evidence_id": queue_item.get("evidence_id") or (candidate or {}).get("evidence_id"),
        "repair_task_id": queue_item.get("repair_task_id"),
        "source_id": queue_item.get("source_id") or (candidate or {}).get("source_id") or (state or {}).get("source_id"),
        "ticker": queue_item.get("ticker") or (candidate or {}).get("ticker") or (state or {}).get("ticker"),
        "company_name": COMPANY_NAMES.get(str(queue_item.get("ticker") or (candidate or {}).get("ticker") or "")),
        "priority": queue_item.get("priority") or "low",
        "item_type": item_type,
        "variable_type": variable_type,
        "sensitive_variable": sensitive,
        "quality_score": queue_item.get("quality_score") if queue_item.get("quality_score") is not None else (state or {}).get("quality_score"),
        "quality_bucket": queue_item.get("quality_bucket") or (state or {}).get("quality_bucket"),
        "lifecycle_status": lifecycle_status,
        "review_status": review_status,
        "quoted_span": quoted_span,
        "quoted_span_preview": queue_item.get("quoted_span_preview") or _preview(quoted_span),
        "source_url": source_url,
        "source_url_missing": not bool(source_url),
        "source_type": queue_item.get("source_type") or (candidate or {}).get("source_type") or ((state or {}).get("metadata") or {}).get("source_type"),
        "linked_variable_pack": variable_pack,
        "link_status": link_status,
        "limitations": limitations,
        "noise_flags": queue_item.get("noise_flags") or [],
        "allowed_usage": queue_item.get("allowed_usage") or (state or {}).get("allowed_usage") or (candidate or {}).get("allowed_usage"),
        "review_reason": queue_item.get("review_reason") or [],
        "recommended_action": queue_item.get("recommended_action"),
        "allowed_actions": list(dict.fromkeys(queue_item.get("allowed_actions") or [])),
        "blocked_actions": SENSITIVE_BLOCKED_ACTIONS if sensitive else ["allow_promotion", "create_pending", "create_paper_order"],
        "sensitive_guard": guard,
        "persisted_in_evidence_store": bool(candidate or state),
        "usable_for_promotion": False,
    }
    normalized["reviewed"] = lifecycle_status in REVIEWED_LIFECYCLE_STATUSES or review_status in {"reviewed", "needs_follow_up", "blocked"}
    normalized["recommended_action"] = recommended_action_for_item(normalized)
    return attach_action_command(normalized)


def build_workbench(
    conn: sqlite3.Connection,
    *,
    tickers: str | None = None,
    ticker: str | None = None,
    include_generated: bool = True,
) -> dict[str, Any]:
    selected = ticker or tickers
    if include_generated:
        try:
            queue = build_review_queue_with_generated_candidates(conn, tickers=selected)
        except Exception:
            # The workbench should remain usable in minimal/local DBs where the
            # Phase 29/30 generated-candidate pipeline is unavailable.
            queue = build_review_queue(conn, ticker=selected)
    elif selected:
        merged: list[dict[str, Any]] = []
        for resolved in resolve_phase25_tickers(selected):
            merged.extend(build_review_queue(conn, ticker=resolved).get("items") or [])
        queue = {"items": merged}
    else:
        queue = build_review_queue(conn)
    candidates, states = _candidate_maps(conn)
    items = [
        normalize_workbench_item(
            item,
            candidate=candidates.get(str(item.get("evidence_id"))),
            state=states.get(str(item.get("evidence_id"))),
        )
        for item in queue.get("items") or []
    ]
    priority_counts = Counter(item.get("priority") for item in items)
    review_required = sum(1 for item in items if item.get("review_status") == "review_required")
    sensitive_count = sum(1 for item in items if item.get("sensitive_variable"))
    download_repair = sum(1 for item in items if item.get("item_type") == "download_repair")
    action_count = sum(1 for item in items if item.get("action_command_dry_run"))
    reviewed_count = sum(1 for item in items if item.get("reviewed"))
    return {
        "summary": {
            "total_workbench_items": len(items),
            "reviewed_items": reviewed_count,
            "remaining_items": max(0, len(items) - reviewed_count),
            "high_priority": priority_counts.get("high", 0),
            "medium_priority": priority_counts.get("medium", 0),
            "low_priority": priority_counts.get("low", 0),
            "sensitive_variable_items": sensitive_count,
            "review_required": review_required,
            "download_repair_tasks": download_repair,
            "dry_run_actions_available": action_count,
            "promotion_allowed_true": sum(1 for item in items if item.get("usable_for_promotion")),
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
        "items": items,
        "safety": {
            "read_only_workbench": True,
            "execute_command_shown_by_default": False,
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
            "real_trade_risk": False,
        },
    }


def filter_workbench_items(
    items: list[dict[str, Any]],
    *,
    priority: str | None = None,
    sensitive_only: bool = False,
    ticker: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    filtered = list(items)
    if priority:
        filtered = [item for item in filtered if item.get("priority") == priority]
    if sensitive_only:
        filtered = [item for item in filtered if item.get("sensitive_variable")]
    if ticker:
        filtered = [item for item in filtered if item.get("ticker") == ticker]
    if limit is not None:
        filtered = filtered[: max(0, int(limit))]
    return filtered


def recommended_first_pass_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if item.get("priority") == "high" or item.get("review_status") == "review_required" or item.get("sensitive_variable"):
            key = str(item.get("workbench_item_id"))
            if key not in seen:
                seen.add(key)
                selected.append(item)
    return selected


def dry_run_workbench_actions(conn: sqlite3.Connection, items: list[dict[str, Any]]) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    for item in items:
        command = item.get("action_command") or {}
        evidence_id = item.get("evidence_id")
        if item.get("item_type") == "download_repair" or item.get("persisted_in_evidence_store") is False:
            actions.append(
                {
                    "evidence_id": evidence_id,
                    "workbench_item_id": item.get("workbench_item_id"),
                    "recommended_action": command.get("recommended_action") or item.get("recommended_action"),
                    "dry_run_result": "pass",
                    "blocked_reason": None,
                    "promotion_allowed_after_action": False,
                    "result": {
                        "allowed": True,
                        "mode": "dry_run",
                        "reason": "phase32 no-op dry-run for non-persisted review or repair item",
                        "safety_checks": {
                            "confirmed_variable_upgrade_blocked": True,
                            "promotion_allowed": False,
                            "paper_order_allowed": False,
                            "pending_allowed": False,
                            "usable_for_promotion": False,
                        },
                        "would_write_audit_log": False,
                    },
                }
            )
            continue
        if not evidence_id or not command.get("dry_run_command"):
            actions.append(
                {
                    "evidence_id": evidence_id,
                    "workbench_item_id": item.get("workbench_item_id"),
                    "recommended_action": command.get("recommended_action") or item.get("recommended_action"),
                    "dry_run_result": "blocked",
                    "blocked_reason": command.get("blocked_reason") or "missing dry-run command",
                    "promotion_allowed_after_action": False,
                }
            )
            continue
        params = action_parameters_for_item(item, command.get("recommended_action"))
        try:
            result = apply_evidence_review_action(
                conn,
                evidence_id=str(evidence_id),
                action=str(params.get("action")),
                reason=params.get("reason"),
                target_usage=params.get("target_usage"),
                dry_run=True,
            )
        except ValueError as exc:
            actions.append(
                {
                    "evidence_id": evidence_id,
                    "workbench_item_id": item.get("workbench_item_id"),
                    "recommended_action": params.get("action"),
                    "dry_run_result": "blocked",
                    "blocked_reason": str(exc),
                    "promotion_allowed_after_action": False,
                }
            )
            continue
        actions.append(
            {
                "evidence_id": evidence_id,
                "workbench_item_id": item.get("workbench_item_id"),
                "recommended_action": params.get("action"),
                "dry_run_result": "pass" if result.get("allowed") else "blocked",
                "blocked_reason": None if result.get("allowed") else result.get("reason"),
                "promotion_allowed_after_action": bool((result.get("after") or {}).get("usable_for_promotion")),
                "result": result,
            }
        )
    conn.rollback()
    blocked = sum(1 for row in actions if row.get("dry_run_result") == "blocked")
    passed = sum(1 for row in actions if row.get("dry_run_result") == "pass")
    return {
        "summary": {
            "items_checked": len(items),
            "dry_run_actions_generated": sum(1 for item in items if (item.get("action_command") or {}).get("dry_run_command")),
            "dry_run_actions_passed": passed,
            "dry_run_actions_blocked": blocked,
            "promotion_allowed_after_actions": sum(1 for row in actions if row.get("promotion_allowed_after_action")),
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
        "actions": actions,
        "safety": {
            "dry_run_wrote_db": False,
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
            "real_trade_risk": False,
        },
    }
