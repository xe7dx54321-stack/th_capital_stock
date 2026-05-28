#!/usr/bin/env python3
"""Phase 37 controlled acquisition task selection."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_evidence_acquisition_readiness import build_acquisition_readiness_score
from smr_evidence_acquisition_task import build_evidence_acquisition_tasks
from smr_wiki import now_ts


DEFAULT_SELECTION_LIMIT = 5
ASP_VARIABLES = {"ASP_price_proxy", "margin_signal"}
VISIBILITY_VARIABLES = {"shipment", "order_visibility"}
CONTEXT_VARIABLES = {"customer_allocation_proxy", "industry_forecast"}


def _clamped_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_SELECTION_LIMIT
    return max(3, min(5, int(limit)))


def _why_selected(task: dict[str, Any], readiness: dict[str, Any]) -> list[str]:
    variable = str(task.get("variable") or "")
    reasons = []
    if int(readiness.get("readiness_score") or 0) >= 72:
        reasons.append("highest readiness")
    if variable == "ASP_price_proxy":
        reasons.append("high impact on valuation support")
        reasons.append("company IR route feasible" if task.get("route_type") in {"company_ir", "investor_relations_record"} else "pricing context route")
    elif variable in VISIBILITY_VARIABLES:
        reasons.append("tests shipment and order visibility")
    elif variable == "customer_allocation_proxy":
        reasons.append("major bear-case uncertainty but must remain proxy-only")
    elif variable == "industry_forecast":
        reasons.append("adds external context without becoming company-specific order evidence")
    elif variable == "official_consensus":
        reasons.append("source availability only; not official consensus data")
    return reasons or ["selected for variable coverage"]


def _skip_reason(task: dict[str, Any]) -> str:
    variable = str(task.get("variable") or "")
    task_type = str(task.get("task_type") or "")
    if variable == "supplier_share":
        return "high impact but low public confirmability; keep manual scenario-only"
    if variable == "official_consensus":
        return "source availability only; do not treat internal proxy as official consensus"
    if task_type == "MARK_NOT_PUBLICLY_CONFIRMABLE":
        return "boundary-marking task; do not execute as evidence acquisition"
    return "outside controlled Phase 37 sample"


def _merged_tasks(conn: sqlite3.Connection, ticker: str) -> list[dict[str, Any]]:
    tasks_payload = build_evidence_acquisition_tasks(conn, ticker)
    readiness_payload = build_acquisition_readiness_score(conn, ticker)
    readiness_by_id = {str(row.get("task_id")): row for row in readiness_payload.get("acquisition_readiness") or []}
    merged = []
    for task in tasks_payload.get("evidence_acquisition_tasks") or []:
        readiness = readiness_by_id.get(str(task.get("task_id"))) or {}
        merged.append({**task, **readiness})
    return sorted(merged, key=lambda row: (-int(row.get("readiness_score") or 0), str(row.get("task_id") or "")))


def _is_selectable(task: dict[str, Any]) -> bool:
    if task.get("task_type") == "MARK_NOT_PUBLICLY_CONFIRMABLE":
        return False
    if task.get("variable") == "supplier_share":
        return False
    return True


def _add_first_matching(selected: list[dict[str, Any]], tasks: list[dict[str, Any]], variables: set[str]) -> None:
    selected_ids = {str(task.get("task_id")) for task in selected}
    for task in tasks:
        if str(task.get("task_id")) in selected_ids:
            continue
        if task.get("variable") in variables and _is_selectable(task):
            selected.append(task)
            return


def build_controlled_acquisition_selection(conn: sqlite3.Connection, ticker: str, *, limit: int | None = None) -> dict[str, Any]:
    ticker = str(ticker or "").strip().upper()
    selection_limit = _clamped_limit(limit)
    tasks = _merged_tasks(conn, ticker)
    selected: list[dict[str, Any]] = []
    _add_first_matching(selected, tasks, ASP_VARIABLES)
    _add_first_matching(selected, tasks, VISIBILITY_VARIABLES)
    _add_first_matching(selected, tasks, CONTEXT_VARIABLES)
    selected_ids = {str(task.get("task_id")) for task in selected}
    for task in tasks:
        if len(selected) >= selection_limit:
            break
        if str(task.get("task_id")) in selected_ids or not _is_selectable(task):
            continue
        selected.append(task)
        selected_ids.add(str(task.get("task_id")))
    selected_ids = {str(task.get("task_id")) for task in selected}
    selected_rows = [
        {
            "task_id": task.get("task_id"),
            "variable": task.get("variable"),
            "task_type": task.get("task_type"),
            "route_type": task.get("route_type"),
            "readiness_score": task.get("readiness_score"),
            "readiness_bucket": task.get("readiness_bucket"),
            "priority": task.get("priority"),
            "execution_mode": "dry_run_first",
            "execution_scope": "source_availability_only" if task.get("variable") == "official_consensus" else "quoted_span_candidate_generation",
            "why_selected": _why_selected(task, task),
            "expected_output": task.get("expected_output"),
            "allowed_usage_target": task.get("allowed_usage_target"),
            "do_not_do": task.get("do_not_do") or [],
        }
        for task in selected
    ]
    skipped_rows = [
        {
            "task_id": task.get("task_id"),
            "variable": task.get("variable"),
            "task_type": task.get("task_type"),
            "readiness_score": task.get("readiness_score"),
            "reason": _skip_reason(task),
        }
        for task in tasks
        if str(task.get("task_id")) not in selected_ids
    ]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "controlled_acquisition_selection": {
            "tasks_available": len(tasks),
            "tasks_selected": len(selected_rows),
            "selection_mode": "top_readiness_with_variable_coverage",
            "selected_tasks": selected_rows,
            "skipped_tasks": skipped_rows,
        },
        "safety": {
            "selection_only": True,
            "supplier_share_confirmed_path_selected": any(row.get("variable") == "supplier_share" for row in selected_rows),
            "official_consensus_impersonated": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }
