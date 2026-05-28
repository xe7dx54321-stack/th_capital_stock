#!/usr/bin/env python3
"""Build Phase 41 follow-up trigger summary."""

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
from smr_research_followup_trigger import build_followup_trigger_summary

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str | None = None) -> dict:
    return build_followup_trigger_summary(conn, ticker=ticker)


def render_markdown(payload: dict) -> str:
    lines = ["# Phase 41 Follow-up Trigger Summary", "", "## Summary"]
    for key, value in (payload.get("summary") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Trigger Rows"])
    for row in payload.get("trigger_rows") or []:
        lines.append(f"- {row.get('ticker')}: {row.get('trigger_type')} / audits={row.get('audit_records')} / {row.get('next_step')}")
    lines.extend(["", "## Excluded Rows"])
    for row in payload.get("excluded_rows") or []:
        lines.append(f"- {row.get('ticker')}: {row.get('reason')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 41 follow-up trigger summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, args.ticker)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
