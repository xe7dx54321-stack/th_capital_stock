#!/usr/bin/env python3
"""Build Phase 48 event refresh tasks."""

from __future__ import annotations

import argparse, json, sqlite3, sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path: sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
from smr_watchlist_event_detector import detect_events
from smr_event_driven_refresh_task import build_event_refresh_tasks

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build_payload(conn, ticker):
    events = detect_events(conn, ticker)
    return build_event_refresh_tasks(events, ticker)

def render_markdown(payload):
    tasks = payload.get("event_refresh_tasks") or {}
    lines = [f"# Phase 48 Event Refresh Tasks: {payload.get('ticker')}", "",
             f"- tasks_generated: {tasks.get('tasks_generated')}",
             f"- research_only_tasks: {tasks.get('research_only_tasks')}",
             "", "## Tasks"]
    for t in tasks.get("tasks") or []:
        lines.append(f"- {t.get('task_type')}: {t.get('target_variable')} (priority={t.get('priority')})")
    return "\n".join(lines).rstrip() + "\n"

def main():
    p = argparse.ArgumentParser(description="Build Phase 48 event refresh tasks")
    p.add_argument("--db-path", default=str(DB_PATH)); p.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args()
    conn = sqlite3.connect(args.db_path)
    try: payload = build_payload(conn, args.ticker)
    finally: conn.close()
    if args.markdown and not args.json: print(render_markdown(payload), end="")
    else: print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0

if __name__ == "__main__": raise SystemExit(main())
