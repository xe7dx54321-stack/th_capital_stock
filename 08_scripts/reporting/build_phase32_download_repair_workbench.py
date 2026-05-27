#!/usr/bin/env python3
"""Build Phase 32 readable download repair workbench packet."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(JOBS_DIR) not in sys.path:
    sys.path.insert(0, str(JOBS_DIR))

from smr_agents import DB_PATH
from smr_download_repair_queue import list_download_repair_tasks, normalize_repair_task, summarize_download_repair_tasks
from smr_wiki import now_ts
from upsert_download_unavailable_repair_tasks import build_payload as build_phase31_repair_tasks

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _notes(task: dict[str, Any]) -> str:
    action = str(task.get("recommended_action") or "")
    if action == "manual_text_needed":
        return "Do not bypass download restrictions; attach clean text manually if available."
    if action == "alternate_source_needed":
        return "Find a compliant alternate official source before creating evidence."
    if action == "needs_ocr_optional":
        return "OCR is optional and must be explicitly enabled later; do not fabricate text."
    return "Retry only through allowed source access paths; do not bypass restrictions."


def _task_row(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "repair_task_id": task.get("repair_task_id"),
        "ticker": task.get("ticker"),
        "source_id": task.get("source_id"),
        "source_url": task.get("source_url"),
        "task_type": task.get("task_type"),
        "reason": task.get("reason"),
        "recommended_action": task.get("recommended_action"),
        "priority": task.get("priority"),
        "status": task.get("status"),
        "notes": _notes(task),
    }


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict[str, Any]:
    tasks = list_download_repair_tasks(conn)
    source = "persisted_repair_queue"
    if not tasks:
        dry_run = build_phase31_repair_tasks(conn, tickers=tickers, execute=False)
        tasks = [normalize_repair_task(task) for task in dry_run.get("tasks") or []]
        source = "phase31_repair_task_dry_run"
    summary = summarize_download_repair_tasks(tasks)
    return {
        "generated_at": now_ts(),
        "source": source,
        "summary": {
            "repair_tasks": len(tasks),
            "manual_text_needed": summary.get("manual_text_needed", 0),
            "alternate_source_needed": summary.get("alternate_source_needed", 0),
            "optional_ocr_needed": summary.get("optional_ocr_needed", 0),
            "download_unavailable": summary.get("download_unavailable", 0),
        },
        "tasks": [_task_row(task) for task in tasks],
        "safety": {
            "auto_download_bypass": False,
            "ocr_default_enabled": False,
            "body_text_fabricated": False,
            "manual_text_needed_is_evidence": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 32 Download Repair Workbench",
        "",
        "## Overall",
        f"- Repair tasks: {summary.get('repair_tasks')}",
        f"- Manual text needed: {summary.get('manual_text_needed')}",
        f"- Alternate source needed: {summary.get('alternate_source_needed')}",
        f"- Optional OCR needed: {summary.get('optional_ocr_needed')}",
        "",
        "## Safety",
        "- Do not bypass download restrictions.",
        "- OCR is not enabled by default.",
        "- Manual text needed is a repair action, not evidence.",
        "",
        "## Tasks",
        "| Ticker | Source | Task Type | Priority | Recommended Action | Notes |",
        "|---|---|---|---|---|---|",
    ]
    for task in payload.get("tasks") or []:
        lines.append(
            f"| {task.get('ticker')} | {task.get('source_id')} | {task.get('task_type')} | {task.get('priority')} | {task.get('recommended_action')} | {task.get('notes')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 32 download repair workbench")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
