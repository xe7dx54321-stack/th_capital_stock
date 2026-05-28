#!/usr/bin/env python3
"""Build Phase 38 300394 repair queue summary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
for path in (LIB_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from upsert_phase38_300394_repair_tasks import REPAIR_TASKS, TARGET_TICKER, WATCHLIST_ID
from smr_agents import DB_PATH
from smr_blocker_repair_queue import list_repair_tasks
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _phase38_tasks(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    tasks = list_repair_tasks(conn, ticker=TARGET_TICKER, watchlist_id=WATCHLIST_ID, limit=200)
    return [task for task in tasks if (task.get("metadata") or {}).get("phase") == 38]


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    tasks = _phase38_tasks(conn)
    return {
        "generated_at": now_ts(),
        "ticker": TARGET_TICKER,
        "repair_queue_summary": {
            "repair_tasks_identified": len(REPAIR_TASKS),
            "repair_tasks_written": len(tasks),
            "duplicates_skipped": 0,
            "root_cause_summary": [
                "evidence not persisted in current state",
                "text cache or generated state may be missing",
                "semantic extraction state requires rerun",
            ],
            "research_deepening_allowed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
            "repair_tasks": tasks,
        },
        "safety": {
            "fake_evidence_written": False,
            "research_conclusion_generated": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("repair_queue_summary") or {}
    lines = [
        "# Phase 38 300394 Repair Queue Summary",
        "",
        f"- Repair tasks identified: {summary.get('repair_tasks_identified')}",
        f"- Repair tasks written: {summary.get('repair_tasks_written')}",
        f"- Research deepening allowed: {summary.get('research_deepening_allowed')}",
        "",
        "## Root Cause Summary",
    ]
    lines.extend(f"- {item}" for item in summary.get("root_cause_summary") or [])
    lines.extend(["", "## Tasks", "| Task Type | Priority | Status | Suggested Fix |", "|---|---|---|---|"])
    for task in summary.get("repair_tasks") or []:
        metadata = task.get("metadata") or {}
        lines.append(
            f"| {metadata.get('repair_task_type')} | {task.get('priority')} | {task.get('status')} | {task.get('suggested_fix')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 38 300394 repair queue summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
