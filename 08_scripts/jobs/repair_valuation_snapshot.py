#!/usr/bin/env python3
"""Phase 9 valuation repair and diagnostics."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
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
from smr_paths import project_path
from smr_valuation import build_valuation_snapshot, diagnose_valuation_snapshot, latest_valuation_snapshot, latest_daily_price, market_for_ticker, valuation_sub_blockers
from smr_wiki import now_ts


SCRIPT_NAME = "repair_valuation_snapshot.py"


def compact_valuation(snapshot: dict[str, Any]) -> dict[str, Any]:
    if not snapshot:
        return {"valuation_status": "missing", "allowed_usage": "context_only", "blockers": ["VALUATION_EVIDENCE_MISSING"]}
    return {
        "valuation_status": snapshot.get("valuation_status"),
        "allowed_usage": snapshot.get("allowed_usage"),
        "price_status": snapshot.get("price_status") or (snapshot.get("metadata") or {}).get("price_status"),
        "current_price": snapshot.get("current_price"),
        "price_trade_date": snapshot.get("price_trade_date") or (snapshot.get("metadata") or {}).get("price_trade_date"),
        "broker_forward_eps_proxy": snapshot.get("broker_forward_eps_proxy"),
        "forward_eps": snapshot.get("forward_eps") or {},
        "peer_set_id": snapshot.get("peer_set_id"),
        "peer_set_status": snapshot.get("peer_set_status"),
        "peer_count_available": snapshot.get("peer_count_available"),
        "peer_count_required": snapshot.get("peer_count_required"),
        "historical_percentile_status": snapshot.get("historical_percentile_status"),
        "valuation_confidence": snapshot.get("valuation_confidence"),
        "missing_data": snapshot.get("missing_data") or [],
        "blockers": [item["code"] for item in valuation_sub_blockers(snapshot)],
    }


def refresh_price_reference(conn: sqlite3.Connection, ticker: str, *, dry_run: bool = True, timeout: int = 180) -> dict[str, Any]:
    market = market_for_ticker(ticker)
    before_price, before_date = latest_daily_price(conn, ticker, market)
    if dry_run:
        return {
            "action": "refresh_price_reference",
            "status": "skipped_dry_run",
            "latest_price": before_price,
            "price_date": before_date,
        }
    script = project_path("08_scripts", "data_harvester", "ah_daily_bar.py")
    command = [sys.executable, str(script), "--days", "10", "--ts-code", ticker]
    try:
        result = subprocess.run(
            command,
            cwd=project_path(),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "action": "refresh_price_reference",
            "status": "failed",
            "reason": f"timeout_after_{timeout}s",
            "latest_price": before_price,
            "price_date": before_date,
        }
    after_price, after_date = latest_daily_price(conn, ticker, market)
    improved = bool(after_date and after_date != before_date)
    if result.returncode == 0 and after_price is not None:
        return {
            "action": "refresh_price_reference",
            "status": "success" if improved else "no_newer_price_available",
            "latest_price": after_price,
            "price_date": after_date,
            "previous_price_date": before_date,
            "command_returncode": result.returncode,
            "stdout_tail": (result.stdout or "")[-600:],
            "stderr_tail": (result.stderr or "")[-600:],
        }
    return {
        "action": "refresh_price_reference",
        "status": "failed",
        "reason": "latest_price_not_available" if after_price is None else f"command_returncode_{result.returncode}",
        "latest_price": after_price,
        "price_date": after_date,
        "previous_price_date": before_date,
        "command_returncode": result.returncode,
        "stdout_tail": (result.stdout or "")[-600:],
        "stderr_tail": (result.stderr or "")[-600:],
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
    actions: list[dict[str, Any]] = []
    if dry_run:
        actions.append(refresh_price_reference(conn, ticker, dry_run=True))
        after = before
        diagnostics_after = diagnostics_before
    else:
        actions.append(refresh_price_reference(conn, ticker, dry_run=False))
        data_health = refresh_system_data_health(conn)
        after = build_valuation_snapshot(conn, ticker, data_health_snapshot=data_health)
        diagnostics_after = diagnose_valuation_snapshot(conn, ticker, data_health_snapshot=data_health, before=after)
        actions.append({"action": "recompute_valuation_snapshot", "status": "success", "allowed_usage": after.get("allowed_usage")})
        actions.append({"action": "attach_fundamentals_snapshot", "status": "success" if after.get("fundamentals_snapshot") else "missing"})
    remaining_blockers = diagnostics_after.get("sub_blockers") or []
    before_blockers = diagnostics_before.get("sub_blockers") or []
    resolved_blockers = sorted(set(before_blockers) - set(remaining_blockers))
    payload = {
        "generated_at": now_ts(),
        "ticker": ticker.upper(),
        "market": market_for_ticker(ticker),
        "mode": "dry_run" if dry_run else "execute",
        "before": compact_valuation(before),
        "diagnostics": diagnostics_before,
        "actions": actions,
        "repair_actions": [item.get("action") for item in actions],
        "after": {
            **compact_valuation(after),
            "resolved_blockers": resolved_blockers,
            "remaining_blockers": remaining_blockers,
        },
        "resolved_blockers": resolved_blockers,
        "needs_manual_review": bool(remaining_blockers),
        "source_repair_id": source_repair_id,
        "repair_queue_updates": [],
    }
    if source_repair_id:
        updated = update_repair_task_metadata(
            conn,
            source_repair_id,
            {
                "phase10_valuation_repair": {
                    "at": payload["generated_at"],
                    "mode": payload["mode"],
                    "diagnostics": diagnostics_before,
                    "after": payload["after"],
                    "actions": actions,
                }
            },
            note="Phase 10 valuation repair updated",
        )
        payload["repair_queue_updates"].append({"repair_id": source_repair_id, "status": updated.get("status")})
    register_snapshot(
        conn,
            entity_type="phase10_valuation_repair" if not dry_run else "phase9_valuation_repair",
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
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--all-open-repair-tasks", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        dry_run = False if args.execute else True
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
