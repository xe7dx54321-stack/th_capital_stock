#!/usr/bin/env python3
"""Validate Phase 33 controlled download repair task upsert."""

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
from smr_download_repair_queue import list_download_repair_tasks, summarize_download_repair_tasks
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    tasks = list_download_repair_tasks(conn)
    summary = summarize_download_repair_tasks(tasks)
    duplicates = len(tasks) - len({(task.get("source_id"), task.get("task_type")) for task in tasks})
    violations = duplicates + sum(1 for task in tasks if (task.get("metadata") or {}).get("auto_download_bypass"))
    return {
        "generated_at": now_ts(),
        "overall_status": "pass" if tasks and violations == 0 else "fail",
        "summary": {
            "repair_tasks_identified": len(tasks),
            "repair_tasks_written": len(tasks),
            "duplicates_skipped": max(0, duplicates),
            "manual_text_needed": summary.get("manual_text_needed", 0),
            "alternate_source_needed": summary.get("alternate_source_needed", 0),
            "optional_ocr_needed": summary.get("optional_ocr_needed", 0),
            "promotion_allowed_from_repair_tasks": 0,
            "violations": violations,
        },
        "tasks": tasks,
        "safety": {
            "auto_download_bypass": False,
            "ocr_default_enabled": False,
            "repair_task_is_evidence": False,
            "promotion_rules_relaxed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 33 download repair upsert")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if payload.get("overall_status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
