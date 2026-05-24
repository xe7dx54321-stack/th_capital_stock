#!/usr/bin/env python3
"""Execute Phase 9 repair queue tasks safely."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase9_data_quality_diagnostics import build_diagnostics
from repair_valuation_snapshot import repair_valuation_for_ticker
from smr_agents import DB_PATH
from smr_bear_case_response import respond_to_bear_case
from smr_blocker_repair_queue import list_repair_tasks, update_repair_task_metadata, update_repair_task_status
from smr_fundamentals import build_fundamentals_snapshot
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts


SCRIPT_NAME = "run_phase9_repair_queue.py"


def action_for_task(task: dict[str, Any]) -> str:
    blocker_type = task.get("blocker_type")
    code = task.get("blocker_code")
    if blocker_type == "valuation" or str(code or "").startswith(("VALUATION", "PRICE", "FORWARD_EPS", "HISTORICAL", "PEER")):
        return "repair_valuation_snapshot"
    if blocker_type == "fundamentals" or code in {
        "FUNDAMENTALS_MISSING_FIELDS",
        "FIELD_NOT_FOUND",
        "FIELD_MAPPING_MISSING",
        "TABLE_NOT_FOUND",
        "PARSE_FAILED",
        "AMBIGUOUS_UNIT",
        "DATA_QUALITY_CORE_GATE",
        "CORE_EVIDENCE_BLOCKER",
    }:
        return "repair_fundamentals_snapshot"
    if blocker_type == "risk" or str(code or "").startswith("HIGH_BEAR_CASE"):
        return "build_bear_case_response"
    if blocker_type in {"data_quality", "evidence"}:
        return "build_data_quality_diagnostics"
    return "manual_triage"


def select_tasks(
    conn: sqlite3.Connection,
    *,
    ticker: str | None = None,
    blocker_code: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    tasks = list_repair_tasks(conn, status="open", watchlist_id="ai_core", limit=max(limit * 4, limit))
    selected = []
    for task in tasks:
        if ticker and task.get("ticker") != ticker.upper():
            continue
        if blocker_code and task.get("blocker_code") != blocker_code:
            continue
        selected.append(task)
        if len(selected) >= limit:
            break
    return selected


def execute_task(conn: sqlite3.Connection, task: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    action = action_for_task(task)
    base = {
        "repair_id": task.get("repair_id"),
        "ticker": task.get("ticker"),
        "blocker_code": task.get("blocker_code"),
        "blocker_type": task.get("blocker_type"),
        "action": action,
    }
    if dry_run:
        return {**base, "mode": "dry_run", "expected_output": expected_output_for_action(action)}

    previous_status = task.get("status")
    update_repair_task_status(conn, task["repair_id"], "in_progress", owner="codex", note=f"Phase 9 executing {action}")
    result: dict[str, Any]
    new_status = "open"
    note = ""
    try:
        if action == "repair_valuation_snapshot":
            result = repair_valuation_for_ticker(conn, task["ticker"], dry_run=False, source_repair_id=task["repair_id"])
            remaining = set((result.get("after") or {}).get("remaining_blockers") or [])
            new_status = "needs_manual_review" if remaining else "in_progress"
            note = "valuation repaired but validation is required before resolution" if not remaining else "valuation repaired but manual review remains"
        elif action == "build_data_quality_diagnostics":
            result = build_diagnostics(conn, task["ticker"], refresh_fundamentals=False)
            new_status = "needs_manual_review" if result.get("root_causes") else "resolved"
            note = "data quality diagnostics generated"
        elif action == "repair_fundamentals_snapshot":
            snapshot = build_fundamentals_snapshot(conn, task["ticker"], prefer_live=True)
            result = {
                "ticker": task["ticker"],
                "snapshot_id": snapshot.get("snapshot_id"),
                "freshness_status": snapshot.get("freshness_status"),
                "missing_fields": snapshot.get("missing_fields") or [],
                "field_missing_reasons": snapshot.get("field_missing_reasons") or {},
            }
            new_status = "needs_manual_review" if result["missing_fields"] else "resolved"
            note = "fundamentals snapshot rebuilt"
        elif action == "build_bear_case_response":
            result = respond_to_bear_case(task["ticker"], {"bear_case_claims": [{"claim_text": task.get("suggested_fix") or "high bear case", "severity": "high"}]})
            new_status = "needs_manual_review"
            note = "bear case response requires validation evidence"
        else:
            result = {"reason": "no automated repair available"}
            new_status = "needs_manual_review"
            note = "manual triage required"
        update_repair_task_metadata(conn, task["repair_id"], {"phase9_execution_result": result}, note=note)
        updated = update_repair_task_status(conn, task["repair_id"], new_status, owner="codex", note=note)
        return {**base, "mode": "execute", "previous_status": previous_status, "new_status": updated.get("status"), "result": result}
    except Exception as exc:
        update_repair_task_status(conn, task["repair_id"], "open", owner="codex", note=f"execution_failed: {exc}")
        return {**base, "mode": "execute", "previous_status": previous_status, "new_status": "open", "error": str(exc)}


def expected_output_for_action(action: str) -> str:
    return {
        "repair_valuation_snapshot": "valuation diagnostics and refreshed snapshot",
        "build_data_quality_diagnostics": "field/evidence/source-level root causes",
        "repair_fundamentals_snapshot": "rebuilt fundamentals snapshot with field-level missing reasons",
        "build_bear_case_response": "structured bear-case response and action effect",
        "manual_triage": "manual repair instructions",
    }.get(action, "repair output")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 9 repair queue")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--blocker-code")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    dry_run = not args.execute
    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        tasks = select_tasks(conn, ticker=args.ticker, blocker_code=args.blocker_code, limit=args.limit)
        results = [execute_task(conn, task, dry_run=dry_run) for task in tasks]
        payload = {
            "generated_at": now_ts(),
            "mode": "dry_run" if dry_run else "execute",
            "tasks_selected": len(tasks),
            "tasks_executed": 0 if dry_run else len(tasks),
            "planned_actions": results if dry_run else [],
            "tasks_updated": [] if dry_run else results,
        }
        register_snapshot(
            conn,
            entity_type="phase9_repair_queue_execution",
            entity_id=args.ticker.upper() if args.ticker else "latest",
            status=payload["mode"],
            source=SCRIPT_NAME,
            payload=payload,
        )
        if not dry_run:
            conn.commit()
        else:
            conn.rollback()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase9 repair queue run complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
