#!/usr/bin/env python3
"""Build Phase 31 download repair queue summary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_download_repair_queue import list_download_repair_tasks, summarize_download_repair_tasks
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None) -> dict:
    tasks = list_download_repair_tasks(conn, ticker=ticker)
    return {
        "generated_at": now_ts(),
        "summary": summarize_download_repair_tasks(tasks),
        "tasks": tasks,
        "safety": {
            "auto_download_bypass": False,
            "ocr_default_enabled": False,
            "manual_text_needed_is_evidence": False,
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 31 Download Repair Queue Summary",
        "",
        "## Overall",
        f"- Repair tasks total: {summary.get('repair_tasks_total')}",
        f"- Open tasks: {summary.get('open_tasks')}",
        f"- Manual text needed: {summary.get('manual_text_needed')}",
        f"- Alternate source needed: {summary.get('alternate_source_needed')}",
        f"- Optional OCR needed: {summary.get('optional_ocr_needed')}",
        "",
        "## Tasks",
        "| Ticker | Source | Task Type | Priority | Status | Recommended Action |",
        "|---|---|---|---|---|---|",
    ]
    for task in payload.get("tasks") or []:
        lines.append(
            f"| {task.get('ticker')} | {task.get('source_id')} | {task.get('task_type')} | {task.get('priority')} | {task.get('status')} | {task.get('recommended_action')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 31 download repair queue summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
