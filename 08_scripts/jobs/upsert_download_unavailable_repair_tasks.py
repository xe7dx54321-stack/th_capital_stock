#!/usr/bin/env python3
"""Upsert Phase 31 download-unavailable repair tasks."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase30_download_unavailable_repair_plan import build_payload as build_repair_plan
from smr_agents import DB_PATH
from smr_download_repair_queue import normalize_repair_task, upsert_download_repair_task
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "upsert_download_unavailable_repair_tasks.py"


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None, execute: bool = False) -> dict:
    plan = build_repair_plan(conn, tickers=tickers)
    sources = plan.get("sources") or []
    tasks = []
    for source in sources:
        task = normalize_repair_task(source)
        if execute:
            task = upsert_download_repair_task(conn, task)
        tasks.append(task)
    return {
        "generated_at": now_ts(),
        "mode": "execute" if execute else "dry_run",
        "summary": {
            "repair_tasks_identified": len(tasks),
            "repair_tasks_written": len(tasks) if execute else 0,
            "dry_run_wrote_db": False if not execute else None,
            "duplicates_prevented": max(0, len(tasks) - len({(task.get("source_id"), task.get("task_type")) for task in tasks})),
        },
        "tasks": tasks,
        "safety": {
            "auto_download_bypass": False,
            "ocr_default_enabled": False,
            "body_text_fabricated": False,
            "evidence_written": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Upsert Phase 31 download repair tasks")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    execute = bool(args.execute and not args.dry_run)
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers, execute=execute)
        register_snapshot(
            conn,
            entity_type="phase31_download_repair_tasks",
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
    log_run(SCRIPT_NAME, "success", "phase31 download repair task upsert complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
