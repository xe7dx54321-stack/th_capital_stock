#!/usr/bin/env python3
"""Build Phase 37 controlled acquisition selection."""

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
from smr_controlled_acquisition_selector import build_controlled_acquisition_selection

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str, limit: int | None = None) -> dict[str, Any]:
    return build_controlled_acquisition_selection(conn, ticker, limit=limit)


def render_markdown(payload: dict[str, Any]) -> str:
    body = payload.get("controlled_acquisition_selection") or {}
    lines = [
        "# Phase 37 Controlled Acquisition Selection",
        "",
        f"## Ticker\n{payload.get('ticker')}",
        "",
        "## Summary",
        f"- Tasks available: {body.get('tasks_available')}",
        f"- Tasks selected: {body.get('tasks_selected')}",
        f"- Selection mode: {body.get('selection_mode')}",
        "",
        "## Selected Tasks",
        "| Task | Variable | Type | Score | Mode | Why |",
        "|---|---|---|---:|---|---|",
    ]
    for task in body.get("selected_tasks") or []:
        lines.append(
            f"| {task.get('task_id')} | {task.get('variable')} | {task.get('task_type')} | "
            f"{task.get('readiness_score')} | {task.get('execution_mode')} | {'; '.join(task.get('why_selected') or [])} |"
        )
    lines.extend(["", "## Skipped Boundary Tasks"])
    for task in (body.get("skipped_tasks") or [])[:8]:
        lines.append(f"- {task.get('task_id')}: {task.get('reason')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 37 controlled acquisition selection")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, limit=args.limit)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
