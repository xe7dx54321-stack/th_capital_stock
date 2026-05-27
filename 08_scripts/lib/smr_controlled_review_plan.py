#!/usr/bin/env python3
"""Phase 33 controlled evidence review plan helpers."""

from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict
from typing import Any

from smr_evidence_action_command_generator import action_parameters_for_item
from smr_evidence_lifecycle import load_semantic_evidence_candidate
from smr_evidence_review_actions import apply_evidence_review_action
from smr_evidence_review_audit import list_evidence_review_audits
from smr_evidence_review_workbench import build_workbench
from smr_sensitive_variable_guard import guard_sensitive_variable, is_sensitive_variable
from smr_wiki import now_ts


PHASE33_ACTOR = "phase33_controlled_review"
PHASE33_REASON_PREFIX = "phase33 controlled review:"
REVIEWED_LIFECYCLE_STATUSES = {
    "approved_evidence",
    "rejected_evidence",
    "downgraded_evidence",
    "marked_noise",
    "needs_better_source",
    "archived",
    "removed",
}


def phase33_reason(action: str, reason: str) -> str:
    return f"{PHASE33_REASON_PREFIX} {action} - {reason}"


def phase33_audits(conn: sqlite3.Connection, *, ticker: str | None = None) -> list[dict[str, Any]]:
    audits = list_evidence_review_audits(conn, ticker=ticker)
    return [
        row
        for row in audits
        if row.get("actor") == PHASE33_ACTOR or str(row.get("reason") or "").startswith(PHASE33_REASON_PREFIX)
    ]


def _item_key(item: dict[str, Any]) -> str:
    return str(item.get("evidence_id") or item.get("workbench_item_id") or "")


def _already_reviewed(item: dict[str, Any]) -> bool:
    if str(item.get("lifecycle_status") or "") in REVIEWED_LIFECYCLE_STATUSES:
        return True
    metadata = ((item.get("sensitive_guard") or {}).get("metadata") or {}) if isinstance(item.get("sensitive_guard"), dict) else {}
    return str(metadata.get("last_review_reason") or "").startswith(PHASE33_REASON_PREFIX)


def _can_execute_item(conn: sqlite3.Connection, item: dict[str, Any], action: str, target_usage: str | None = None) -> tuple[bool, str]:
    evidence_id = item.get("evidence_id")
    if not evidence_id:
        return False, "missing evidence_id"
    if item.get("persisted_in_evidence_store") is False:
        return False, "not persisted in evidence store"
    try:
        result = apply_evidence_review_action(
            conn,
            evidence_id=str(evidence_id),
            action=action,
            target_usage=target_usage,
            reason=phase33_reason(action, "plan dry-run validation"),
            actor=PHASE33_ACTOR,
            dry_run=True,
        )
    except ValueError as exc:
        return False, str(exc)
    return bool(result.get("allowed")), str(result.get("reason") or "allowed")


def _make_plan_item(
    item: dict[str, Any],
    *,
    action: str,
    reason_for_selection: list[str],
    target_usage: str | None = None,
) -> dict[str, Any]:
    action_reason = phase33_reason(action, "; ".join(reason_for_selection))
    params = action_parameters_for_item(item, action)
    if target_usage is not None:
        params["target_usage"] = target_usage
    params["reason"] = action_reason
    return {
        "plan_item_id": f"phase33_plan_{item.get('evidence_id')}",
        "workbench_item_id": item.get("workbench_item_id"),
        "evidence_id": item.get("evidence_id"),
        "ticker": item.get("ticker"),
        "priority": item.get("priority"),
        "variable_type": item.get("variable_type"),
        "sensitive_variable": bool(item.get("sensitive_variable")),
        "current_lifecycle_status": item.get("lifecycle_status"),
        "current_review_status": item.get("review_status"),
        "quality_score": item.get("quality_score"),
        "quality_bucket": item.get("quality_bucket"),
        "recommended_action": action,
        "action_mode": "execute_candidate",
        "target_usage": params.get("target_usage"),
        "reason": params.get("reason"),
        "reason_for_selection": list(dict.fromkeys(reason_for_selection)),
        "source_url": item.get("source_url"),
        "quoted_span_preview": item.get("quoted_span_preview"),
        "safety_expectations": {
            "promotion_allowed_after_action": False,
            "new_pending_created": False,
            "paper_order_created": False,
        },
        "blocked_actions": item.get("blocked_actions") or [],
        "action_parameters": params,
    }


def _skip_item(item: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "plan_item_id": f"phase33_skip_{item.get('evidence_id') or item.get('workbench_item_id')}",
        "workbench_item_id": item.get("workbench_item_id"),
        "evidence_id": item.get("evidence_id"),
        "repair_task_id": item.get("repair_task_id"),
        "ticker": item.get("ticker"),
        "priority": item.get("priority"),
        "variable_type": item.get("variable_type"),
        "sensitive_variable": bool(item.get("sensitive_variable")),
        "current_lifecycle_status": item.get("lifecycle_status"),
        "current_review_status": item.get("review_status"),
        "recommended_action": item.get("recommended_action"),
        "action_mode": "skip",
        "skip_reason": reason,
    }


def _eligible_items(conn: sqlite3.Connection, items: list[dict[str, Any]], skipped: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible = []
    for item in items:
        if item.get("item_type") == "download_repair":
            skipped.append(_skip_item(item, "download repair is handled by the controlled repair upsert job"))
            continue
        if not item.get("evidence_id"):
            skipped.append(_skip_item(item, "missing evidence_id"))
            continue
        if item.get("persisted_in_evidence_store") is False:
            skipped.append(_skip_item(item, "review-only/generated item is not safe for execute action"))
            continue
        if _already_reviewed(item):
            skipped.append(_skip_item(item, "already reviewed or terminal lifecycle status"))
            continue
        if not load_semantic_evidence_candidate(conn, str(item.get("evidence_id"))):
            skipped.append(_skip_item(item, "semantic evidence candidate not found in persistent store"))
            continue
        eligible.append(item)
    return eligible


def _pick_first(
    conn: sqlite3.Connection,
    items: list[dict[str, Any]],
    *,
    selected: list[dict[str, Any]],
    seen: set[str],
    action: str,
    reason: list[str],
    predicate,
    target_usage: str | None = None,
) -> bool:
    for item in items:
        key = _item_key(item)
        if not key or key in seen or not predicate(item):
            continue
        ok, _ = _can_execute_item(conn, item, action, target_usage)
        if not ok:
            continue
        selected.append(_make_plan_item(item, action=action, target_usage=target_usage, reason_for_selection=reason))
        seen.add(key)
        return True
    return False


def build_controlled_review_plan(
    conn: sqlite3.Connection,
    *,
    tickers: str | None = None,
    limit: int = 8,
    include_generated: bool = True,
) -> dict[str, Any]:
    """Build a small, guarded Phase 33 execute plan from Phase 32 workbench items."""

    requested_limit = max(1, min(int(limit or 8), 8))
    workbench = build_workbench(conn, tickers=tickers, include_generated=include_generated)
    items = list(workbench.get("items") or [])
    skipped: list[dict[str, Any]] = []
    eligible = _eligible_items(conn, items, skipped)
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    high_sensitive = [item for item in eligible if item.get("priority") == "high" and item.get("sensitive_variable")]
    for item in high_sensitive[:3]:
        if len(selected) >= requested_limit:
            break
        key = _item_key(item)
        if key in seen:
            continue
        ok, _ = _can_execute_item(conn, item, "downgrade_usage", "context_only")
        if not ok:
            continue
        selected.append(
            _make_plan_item(
                item,
                action="downgrade_usage",
                target_usage="context_only",
                reason_for_selection=["high_priority", "sensitive_variable", "guarded_usage_downgrade"],
            )
        )
        seen.add(key)

    if len(selected) < requested_limit:
        _pick_first(
            conn,
            eligible,
            selected=selected,
            seen=seen,
            action="approve_evidence",
            reason=["non_sensitive_variable", "usable_quality", "approve_without_promotion"],
            predicate=lambda item: not item.get("sensitive_variable") and item.get("quality_bucket") == "usable",
        )

    if len(selected) < requested_limit:
        _pick_first(
            conn,
            eligible,
            selected=selected,
            seen=seen,
            action="request_better_source",
            reason=["source_quality_spot_check", "repair_lifecycle_validation"],
            predicate=lambda item: not item.get("sensitive_variable"),
        )

    if len(selected) < requested_limit:
        _pick_first(
            conn,
            eligible,
            selected=selected,
            seen=seen,
            action="downgrade_usage",
            target_usage="context_only",
            reason=["weak_but_usable", "conservative_usage_downgrade"],
            predicate=lambda item: not item.get("sensitive_variable") and item.get("quality_bucket") in {"weak_but_usable", "review_required"},
        )

    if len(selected) < requested_limit:
        _pick_first(
            conn,
            eligible,
            selected=selected,
            seen=seen,
            action="reject_evidence",
            reason=["controlled_negative_review_sample", "reject_without_physical_delete"],
            predicate=lambda item: not item.get("sensitive_variable"),
        )

    if len(selected) < requested_limit:
        _pick_first(
            conn,
            eligible,
            selected=selected,
            seen=seen,
            action="mark_as_noise",
            reason=["controlled_noise_review_sample", "block_variable_pack_usage"],
            predicate=lambda item: not item.get("sensitive_variable"),
        )

    if len(selected) < requested_limit:
        for item in eligible:
            if len(selected) >= requested_limit:
                break
            key = _item_key(item)
            if key in seen or item.get("sensitive_variable"):
                continue
            ok, _ = _can_execute_item(conn, item, "approve_evidence")
            if not ok:
                continue
            selected.append(
                _make_plan_item(
                    item,
                    action="approve_evidence",
                    reason_for_selection=["fill_remaining_sample", "non_sensitive_variable", "approve_without_promotion"],
                )
            )
            seen.add(key)

    reason_counts: Counter[str] = Counter(reason for item in selected for reason in item.get("reason_for_selection") or [])
    action_counts = Counter(item.get("recommended_action") for item in selected)
    sensitive_count = sum(1 for item in selected if item.get("sensitive_variable"))
    high_count = sum(1 for item in selected if item.get("priority") == "high")
    request_count = action_counts.get("request_better_source", 0)
    skip_reasons = Counter(item.get("skip_reason") for item in skipped)
    warnings = []
    if not sensitive_count:
        warnings.append("no sensitive variable item available for controlled sample")
    if not request_count:
        warnings.append("no request_better_source item selected; download repair is validated by repair upsert")
    if not any(action in action_counts for action in ("downgrade_usage", "reject_evidence")):
        warnings.append("no downgrade_usage or reject_evidence action selected")
    if not any(item.get("current_review_status") == "review_required" for item in selected):
        skipped_review = [item for item in skipped if item.get("current_review_status") == "review_required"]
        if skipped_review:
            warnings.append("review_required item skipped because it is not persisted and cannot be safely executed")

    return {
        "generated_at": now_ts(),
        "summary": {
            "planned_items": len(selected),
            "planned_actions": len(selected),
            "high_priority": high_count,
            "sensitive_items": sensitive_count,
            "review_required": sum(1 for item in selected if item.get("current_review_status") == "review_required"),
            "request_better_source": request_count,
            "downgrade_or_reject": action_counts.get("downgrade_usage", 0) + action_counts.get("reject_evidence", 0),
            "skipped_items": len(skipped),
            "promotion_allowed_expected": False,
            "new_pending_expected": False,
            "paper_order_expected": False,
        },
        "filters": {"tickers": tickers, "limit": requested_limit, "include_generated": include_generated},
        "plan_items": selected,
        "skipped_items": skipped,
        "action_counts": dict(action_counts),
        "selection_reason_counts": dict(reason_counts),
        "skip_reasons": dict(skip_reasons),
        "warnings": warnings,
        "workbench_summary": workbench.get("summary") or {},
        "safety": {
            "controlled_sample_only": True,
            "execute_all_queue_items": False,
            "promotion_allowed_after_action": False,
            "new_pending_created": False,
            "paper_order_created": False,
            "real_trade_risk": False,
        },
    }


def summarize_phase33_audit_deltas(audits: list[dict[str, Any]]) -> dict[str, Any]:
    action_counts = Counter(row.get("action") for row in audits)
    after_counts = Counter(row.get("after_status") for row in audits)
    return {
        "audit_records": len(audits),
        "approved_evidence_delta": after_counts.get("approved_evidence", 0),
        "rejected_evidence_delta": after_counts.get("rejected_evidence", 0),
        "downgraded_evidence_delta": after_counts.get("downgraded_evidence", 0),
        "marked_noise_delta": after_counts.get("marked_noise", 0),
        "needs_better_source_delta": after_counts.get("needs_better_source", 0),
        "actions_by_type": dict(action_counts),
        "promotion_allowed_true_delta": sum(1 for row in audits if row.get("promotion_allowed_after_action")),
        "new_pending_created": 0,
        "paper_order_created": 0,
    }


def phase33_audit_rows(audits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "audit_id": row.get("audit_id"),
            "evidence_id": row.get("evidence_id"),
            "ticker": row.get("ticker"),
            "action": row.get("action"),
            "before_lifecycle_status": row.get("before_status"),
            "after_lifecycle_status": row.get("after_status"),
            "before_allowed_usage": row.get("before_allowed_usage"),
            "after_allowed_usage": row.get("after_allowed_usage"),
            "promotion_allowed_after_action": bool(row.get("promotion_allowed_after_action")),
            "reason": row.get("reason"),
            "reviewed_at": row.get("created_at"),
        }
        for row in audits
    ]


def grouped_audits_by_ticker(audits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in audits:
        grouped[str(row.get("ticker") or "UNKNOWN")].append(row)
    rows = []
    for ticker, records in sorted(grouped.items()):
        actions = Counter(row.get("action") for row in records)
        if actions.get("downgrade_usage") or actions.get("mark_as_noise") or actions.get("reject_evidence"):
            variable_pack_effect = "usage_downgraded"
        elif actions.get("request_better_source"):
            variable_pack_effect = "needs_better_source"
        elif actions.get("approve_evidence"):
            variable_pack_effect = "approved_without_promotion"
        else:
            variable_pack_effect = "unchanged"
        rows.append(
            {
                "ticker": ticker,
                "reviewed_evidence": len({row.get("evidence_id") for row in records}),
                "actions_by_type": dict(actions),
                "variable_pack_effect": variable_pack_effect,
                "expectation_gap_effect": "unchanged",
                "why_not_upgraded": [
                    "supplier share still not disclosed",
                    "ASP still missing",
                    "customer allocation still missing",
                ],
            }
        )
    return rows
