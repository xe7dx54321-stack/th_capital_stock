#!/usr/bin/env python3
"""Phase 10 repair resolution checks.

Resolution is intentionally conservative: a repair task is marked resolved only
when a validation payload proves the original blocker disappeared and was not
just replaced by more specific sub-blockers.
"""

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
from smr_blocker_repair_queue import list_repair_tasks, resolve_repair_task_after_validation, update_repair_task_status
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts


SCRIPT_NAME = "run_phase10_repair_resolution.py"
UMBRELLA_TO_SUB_BLOCKERS = {
    "VALUATION_NOT_PROMOTION_ELIGIBLE": {
        "PRICE_STALE",
        "VALUATION_STALE",
        "FORWARD_EPS_MISSING",
        "HISTORICAL_PERCENTILE_MISSING",
        "HISTORICAL_PRICE_HISTORY_MISSING",
        "HISTORICAL_FUNDAMENTALS_MISSING",
        "HISTORICAL_REVENUE_MISSING",
        "HISTORICAL_EQUITY_MISSING",
        "HISTORICAL_SAMPLE_INSUFFICIENT",
        "HISTORICAL_METRIC_NOT_MEANINGFUL",
        "HISTORICAL_PERCENTILE_PARTIAL",
        "PEER_SET_MISSING",
        "PEER_SET_CONFIG_MISSING",
        "PEER_DATA_MISSING",
        "PEER_PRICE_MISSING",
        "PEER_FUNDAMENTALS_MISSING",
        "PEER_MULTIPLES_MISSING",
        "PEER_COUNT_INSUFFICIENT",
        "PEER_PARTIAL_DATA",
        "VALUATION_CONFIDENCE_LOW",
    },
    "HIGH_BEAR_CASE": {"HIGH_BEAR_CASE_UNRESOLVED", "HIGH_BEAR_CASE_PARTIALLY_MITIGATED"},
    "DATA_QUALITY_RISK": {
        "FIELD_MAPPING_MISSING",
        "FIELD_NOT_FOUND",
        "TABLE_NOT_FOUND",
        "AMBIGUOUS_UNIT",
        "MISSING_SOURCE_EVIDENCE_ID",
        "EVIDENCE_QUALITY_LOW",
    },
}


def replacement_blockers_for(blocker_code: str, validation_blockers: list[str]) -> list[str]:
    sub_codes = UMBRELLA_TO_SUB_BLOCKERS.get(blocker_code, set())
    return [code for code in validation_blockers if code in sub_codes and code != blocker_code]


def resolve_tasks(
    conn: sqlite3.Connection,
    *,
    ticker: str | None = None,
    validation_blockers: list[str] | None = None,
    validation_provided: bool | None = None,
    dry_run: bool = True,
    limit: int = 20,
) -> dict[str, Any]:
    tasks = list_repair_tasks(conn, status=None, ticker=ticker, watchlist_id="ai_core", limit=limit)
    blockers = [str(item) for item in validation_blockers or [] if str(item).strip()]
    has_validation = validation_provided if validation_provided is not None else validation_blockers is not None
    results: list[dict[str, Any]] = []
    for task in tasks:
        if task.get("status") not in {"open", "in_progress", "needs_manual_review"}:
            continue
        replacements = replacement_blockers_for(str(task.get("blocker_code") or ""), blockers)
        is_resolved = has_validation and task.get("blocker_code") not in blockers and not replacements
        resolution_check = {
            "repair_id": task.get("repair_id"),
            "ticker": task.get("ticker"),
            "blocker_code": task.get("blocker_code"),
            "previous_status": task.get("status"),
            "resolution_check": {
                "validation_provided": has_validation,
                "umbrella_blocker_removed": task.get("blocker_code") not in blockers,
                "remaining_sub_blockers": replacements,
                "is_resolved": is_resolved,
                "reason": None if has_validation else "needs_validation_before_resolution",
            },
        }
        if dry_run:
            resolution_check["new_status"] = task.get("status")
        else:
            if has_validation:
                updated = resolve_repair_task_after_validation(
                    conn,
                    task["repair_id"],
                    validation_blockers=blockers,
                    replacement_blockers=replacements,
                    reason="Phase 10 repaired-candidate validation",
                )
            else:
                updated = update_repair_task_status(
                    conn,
                    task["repair_id"],
                    "needs_manual_review",
                    owner="codex",
                    note="Phase 10 resolution requires validation blockers before changing resolved state",
                )
            resolution_check["new_status"] = updated.get("status")
        results.append(resolution_check)
    return {
        "generated_at": now_ts(),
        "mode": "dry_run" if dry_run else "execute",
        "ticker": ticker.upper() if ticker else None,
        "validation_blockers": blockers,
        "tasks_checked": len(results),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve Phase 10 repair queue tasks after validation")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--validation-blockers", default="")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    blockers = [item.strip() for item in args.validation_blockers.split(",") if item.strip()]
    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        payload = resolve_tasks(
            conn,
            ticker=args.ticker,
            validation_blockers=blockers,
            validation_provided=bool(args.validation_blockers.strip()),
            dry_run=not args.execute,
            limit=args.limit,
        )
        register_snapshot(
            conn,
            entity_type="phase10_repair_resolution",
            entity_id=(args.ticker or "latest").upper(),
            status=payload["mode"],
            source=SCRIPT_NAME,
            payload=payload,
        )
        if args.execute:
            conn.commit()
        else:
            conn.rollback()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase10 repair resolution complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
