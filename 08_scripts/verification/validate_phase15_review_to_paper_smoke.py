#!/usr/bin/env python3
"""Phase 15 smoke validation for review-to-paper lifecycle."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from smr_agents import DB_PATH
from smr_human_review_workflow import apply_human_review_action, list_review_queue
from smr_paper_portfolio import apply_approved_recommendations, create_order_for_approved_recommendation
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts


SCRIPT_NAME = "validate_phase15_review_to_paper_smoke.py"


def find_reduced_size_pending(conn: sqlite3.Connection, ticker: str) -> dict:
    ticker = ticker.upper()
    matches = [
        item for item in list_review_queue(conn)
        if str(item.get("ticker") or "").upper() == ticker and item.get("promotion_mode") == "reduced_size_pending"
    ]
    if matches:
        return matches[0]
    return {}


def validate_smoke(conn: sqlite3.Connection, ticker: str, *, execute: bool = False) -> dict:
    pending = find_reduced_size_pending(conn, ticker)
    if not pending:
        return {
            "generated_at": now_ts(),
            "ticker": ticker,
            "mode": "execute" if execute else "dry_run",
            "stages": {"reduced_size_pending_found": False},
            "skip_reason": "no reduced-size pending recommendation found",
        }
    rec_id = pending["recommendation_id"]
    guard_order = create_order_for_approved_recommendation(
        conn,
        {
            "recommendation_id": rec_id,
            "ticker": pending.get("ticker"),
            "market": pending.get("market"),
            "action": pending.get("action"),
            "suggested_position_pct": pending.get("suggested_position_pct"),
            "metadata": {"phase15_guard_probe": True},
        },
        dry_run=not execute,
    )
    manual = apply_human_review_action(
        conn,
        recommendation_id=rec_id,
        action="approve_paper",
        reviewer="phase15_smoke",
        note="phase15 review-to-paper smoke approval",
        dry_run=not execute,
    )
    result = {
        "generated_at": now_ts(),
        "ticker": ticker,
        "mode": "execute" if execute else "dry_run",
        "recommendation_id": rec_id,
        "stages": {
            "reduced_size_pending_found": True,
            "auto_approval_blocked": not bool(pending.get("auto_approval_allowed")),
            "paper_order_blocked_before_approval": guard_order.get("status") == "blocked_not_approved",
            "manual_approval_dry_run": not execute and bool(manual.get("allowed")),
            "manual_approval_applied": execute and manual.get("after_status") == "approved_paper",
        },
        "would_create_order": bool(not execute and manual.get("allowed")),
        "would_open_position": bool(not execute and manual.get("allowed")),
        "position_pct": pending.get("suggested_position_pct"),
        "manual_review_result": manual,
        "paper_order_guard_probe": guard_order,
    }
    if execute:
        paper = apply_approved_recommendations(conn, limit=100, execute=True)
        order = next((item for item in paper.get("orders") or [] if item.get("recommendation_id") == rec_id), {})
        execution = next((item for item in paper.get("executions") or [] if item.get("order_id") == order.get("order_id")), {})
        result["paper_application"] = paper
        result["paper_order_id"] = order.get("order_id")
        result["paper_position_id"] = execution.get("position_id")
        result["stages"].update(
            {
                "paper_order_created": bool(order.get("created")),
                "paper_position_opened": bool(execution.get("executed") and execution.get("position_id")),
                "ledger_written": True,
            }
        )
    else:
        conn.rollback()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 15 review-to-paper smoke")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default="09988.HK")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    try:
        payload = validate_smoke(conn, args.ticker, execute=args.execute)
        register_snapshot(
            conn,
            entity_type="phase15_review_to_paper_smoke",
            entity_id=args.ticker,
            status=str(payload.get("mode")),
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
    log_run(SCRIPT_NAME, "success", "phase15 review-to-paper smoke complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
