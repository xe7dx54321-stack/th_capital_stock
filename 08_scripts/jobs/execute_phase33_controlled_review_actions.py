#!/usr/bin/env python3
"""Execute a small Phase 33 controlled evidence review sample."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_controlled_review_plan import PHASE33_ACTOR, build_controlled_review_plan
from smr_evidence_review_actions import apply_evidence_review_action
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_sensitive_variable_guard import guard_candidates
from smr_evidence_lifecycle import list_semantic_evidence_candidates
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "execute_phase33_controlled_review_actions.py"


def _guard_allows_execution(conn: sqlite3.Connection) -> tuple[bool, dict[str, Any]]:
    checks = guard_candidates(list_semantic_evidence_candidates(conn))
    live_violations = [
        row
        for row in checks
        if row.get("violations")
        and not all("allowed_usage too permissive" in str(v) for v in row.get("violations") or [])
    ]
    return not live_violations, {"checks": checks, "violations": live_violations}


def _result_row(plan_item: dict[str, Any], result: dict[str, Any], *, audit_written: bool) -> dict[str, Any]:
    return {
        "plan_item_id": plan_item.get("plan_item_id"),
        "evidence_id": plan_item.get("evidence_id"),
        "ticker": plan_item.get("ticker"),
        "action": plan_item.get("recommended_action"),
        "allowed": bool(result.get("allowed")),
        "dry_run_result": "pass" if result.get("allowed") else "blocked",
        "before_lifecycle_status": (result.get("before") or {}).get("lifecycle_status"),
        "after_lifecycle_status": (result.get("after") or {}).get("lifecycle_status"),
        "before_allowed_usage": (result.get("before") or {}).get("allowed_usage"),
        "after_allowed_usage": (result.get("after") or {}).get("allowed_usage"),
        "audit_written": audit_written,
        "audit_id": (result.get("audit_record") or {}).get("audit_id"),
        "blocked_reason": None if result.get("allowed") else result.get("reason"),
        "promotion_allowed_after_action": bool((result.get("after") or {}).get("usable_for_promotion")),
    }


def build_payload(
    conn: sqlite3.Connection,
    *,
    limit: int = 8,
    tickers: str | None = None,
    execute: bool = False,
) -> dict[str, Any]:
    plan = build_controlled_review_plan(conn, tickers=tickers, limit=limit)
    guard_ok, guard = _guard_allows_execution(conn)
    action_results: list[dict[str, Any]] = []
    attempted = 0
    executed = 0
    blocked = 0
    audit_written = 0
    lifecycle_updated = 0
    mode = "execute" if execute else "dry_run"

    for plan_item in plan.get("plan_items") or []:
        attempted += 1
        if execute and not guard_ok:
            blocked += 1
            action_results.append(
                {
                    "plan_item_id": plan_item.get("plan_item_id"),
                    "evidence_id": plan_item.get("evidence_id"),
                    "ticker": plan_item.get("ticker"),
                    "action": plan_item.get("recommended_action"),
                    "allowed": False,
                    "dry_run_result": "blocked",
                    "blocked_reason": "sensitive guard failed before execution",
                    "promotion_allowed_after_action": False,
                    "audit_written": False,
                }
            )
            continue
        try:
            result = apply_evidence_review_action(
                conn,
                evidence_id=str(plan_item.get("evidence_id")),
                action=str(plan_item.get("recommended_action")),
                reason=plan_item.get("reason"),
                target_usage=plan_item.get("target_usage"),
                actor=PHASE33_ACTOR,
                dry_run=not execute,
            )
        except ValueError as exc:
            blocked += 1
            action_results.append(
                {
                    "plan_item_id": plan_item.get("plan_item_id"),
                    "evidence_id": plan_item.get("evidence_id"),
                    "ticker": plan_item.get("ticker"),
                    "action": plan_item.get("recommended_action"),
                    "allowed": False,
                    "dry_run_result": "blocked",
                    "blocked_reason": str(exc),
                    "promotion_allowed_after_action": False,
                    "audit_written": False,
                }
            )
            continue
        if not result.get("allowed"):
            blocked += 1
            action_results.append(_result_row(plan_item, result, audit_written=False))
            continue
        did_write = bool(execute and result.get("audit_record"))
        action_results.append(_result_row(plan_item, result, audit_written=did_write))
        if execute:
            executed += 1
            audit_written += int(did_write)
            lifecycle_updated += int(bool(result.get("stored_lifecycle")))

    summary = {
        "planned_actions": len(plan.get("plan_items") or []),
        "actions_attempted": attempted,
        "actions_executed": executed,
        "actions_blocked": blocked,
        "audit_records_written": audit_written,
        "lifecycle_status_updated": lifecycle_updated,
        "promotion_allowed_after_actions": sum(1 for row in action_results if row.get("promotion_allowed_after_action")),
        "new_pending_created": 0,
        "paper_order_created": 0,
    }
    return {
        "generated_at": now_ts(),
        "mode": mode,
        "summary": summary,
        "plan_summary": plan.get("summary") or {},
        "action_results": action_results,
        "skipped_items": plan.get("skipped_items") or [],
        "sensitive_guard": {
            "pre_execution_passed": guard_ok,
            "violations": len(guard.get("violations") or []),
        },
        "safety": {
            "controlled_plan_only": True,
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute Phase 33 controlled review actions")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    execute = bool(args.execute and not args.dry_run)
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, limit=args.limit, tickers=args.tickers, execute=execute)
        register_snapshot(
            conn,
            entity_type="phase33_controlled_review_execution",
            entity_id=args.tickers or "supply_chain_pilot",
            status="execute" if execute else "dry_run",
            source=SCRIPT_NAME,
            payload=payload,
        )
        if execute:
            conn.commit()
        else:
            conn.rollback()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase33 controlled review actions processed", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
