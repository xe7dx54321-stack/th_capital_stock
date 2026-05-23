#!/usr/bin/env python3
"""Phase 9 valuation repair and diagnostics."""

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
from smr_blocker_repair_queue import list_repair_tasks, update_repair_task_metadata
from smr_data_health import refresh_system_data_health
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_valuation import build_valuation_snapshot, diagnose_valuation_snapshot, latest_valuation_snapshot, market_for_ticker, valuation_sub_blockers
from smr_wiki import now_ts


SCRIPT_NAME = "repair_valuation_snapshot.py"


def compact_valuation(snapshot: dict[str, Any]) -> dict[str, Any]:
    if not snapshot:
        return {"valuation_status": "missing", "allowed_usage": "context_only", "blockers": ["VALUATION_EVIDENCE_MISSING"]}
    return {
        "valuation_status": snapshot.get("valuation_status"),
        "allowed_usage": snapshot.get("allowed_usage"),
        "current_price": snapshot.get("current_price"),
        "price_trade_date": snapshot.get("price_trade_date") or (snapshot.get("metadata") or {}).get("price_trade_date"),
        "broker_forward_eps_proxy": snapshot.get("broker_forward_eps_proxy"),
        "valuation_confidence": snapshot.get("valuation_confidence"),
        "missing_data": snapshot.get("missing_data") or [],
        "blockers": [item["code"] for item in valuation_sub_blockers(snapshot)],
    }


def repair_valuation_for_ticker(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    dry_run: bool = True,
    source_repair_id: str | None = None,
) -> dict[str, Any]:
    before = latest_valuation_snapshot(conn, ticker)
    data_health = refresh_system_data_health(conn)
    diagnostics_before = diagnose_valuation_snapshot(conn, ticker, data_health_snapshot=data_health, before=before)
    repair_actions = ["recompute_valuation_snapshot", "attach_fundamentals_snapshot", "refresh_price_reference"]
    if dry_run:
        after = before
        diagnostics_after = diagnostics_before
    else:
        after = build_valuation_snapshot(conn, ticker, data_health_snapshot=data_health)
        diagnostics_after = diagnose_valuation_snapshot(conn, ticker, data_health_snapshot=data_health, before=after)
    remaining_blockers = diagnostics_after.get("sub_blockers") or []
    payload = {
        "generated_at": now_ts(),
        "ticker": ticker.upper(),
        "market": market_for_ticker(ticker),
        "mode": "dry_run" if dry_run else "execute",
        "before": compact_valuation(before),
        "diagnostics": diagnostics_before,
        "repair_actions": repair_actions,
        "after": {
            **compact_valuation(after),
            "remaining_blockers": remaining_blockers,
        },
        "resolved_blockers": sorted(set(diagnostics_before.get("sub_blockers") or []) - set(remaining_blockers)),
        "source_repair_id": source_repair_id,
    }
    if source_repair_id:
        update_repair_task_metadata(
            conn,
            source_repair_id,
            {
                "phase9_valuation_repair": {
                    "at": payload["generated_at"],
                    "mode": payload["mode"],
                    "diagnostics": diagnostics_before,
                    "after": payload["after"],
                }
            },
            note="Phase 9 valuation repair diagnostics updated",
        )
    register_snapshot(
        conn,
        entity_type="phase9_valuation_repair",
        entity_id=ticker.upper(),
        status=payload["after"].get("allowed_usage") or "unknown",
        source=SCRIPT_NAME,
        payload=payload,
    )
    return payload


def valuation_tasks(conn: sqlite3.Connection, limit: int = 50) -> list[dict[str, Any]]:
    tasks = list_repair_tasks(conn, status="open", watchlist_id="ai_core", limit=limit)
    return [task for task in tasks if task.get("blocker_type") == "valuation" or str(task.get("blocker_code") or "").startswith("VALUATION") or task.get("blocker_code") == "PRICE_STALE"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair or diagnose valuation snapshots")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--all-open-repair-tasks", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        dry_run = True if args.dry_run else False
        if args.all_open_repair_tasks:
            results = [
                repair_valuation_for_ticker(conn, task["ticker"], dry_run=dry_run, source_repair_id=task["repair_id"])
                for task in valuation_tasks(conn)
            ]
            payload = {
                "generated_at": now_ts(),
                "mode": "dry_run" if dry_run else "execute",
                "task_count": len(results),
                "results": results,
            }
        else:
            ticker = (args.ticker or "09988.HK").upper()
            payload = repair_valuation_for_ticker(conn, ticker, dry_run=dry_run)
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase9 valuation repair complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
