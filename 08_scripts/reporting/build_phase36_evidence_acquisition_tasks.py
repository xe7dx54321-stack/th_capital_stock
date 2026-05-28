#!/usr/bin/env python3
"""Build Phase 36 evidence acquisition tasks."""

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
from smr_evidence_acquisition_task import build_evidence_acquisition_tasks

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str) -> dict[str, Any]:
    return build_evidence_acquisition_tasks(conn, ticker)


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 36 Evidence Acquisition Tasks",
        "",
        f"## Ticker\n{payload.get('ticker')} / {payload.get('company_name')}",
        "",
        "## Summary",
        f"- Tasks: {summary.get('tasks')}",
        f"- High priority tasks: {summary.get('high_priority_tasks')}",
        f"- Manual research required: {summary.get('manual_research_required')}",
        f"- Not publicly confirmable: {summary.get('not_publicly_confirmable')}",
        "",
        "## Tasks",
        "| Task | Variable | Type | Priority | Expected Output | Do Not Do |",
        "|---|---|---|---|---|---|",
    ]
    for task in payload.get("evidence_acquisition_tasks") or []:
        lines.append(
            f"| {task.get('task_id')} | {task.get('variable')} | {task.get('task_type')} | {task.get('priority')} | "
            f"{task.get('expected_output')} | {'; '.join(task.get('do_not_do') or [])} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 36 evidence acquisition tasks")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", required=True)
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
