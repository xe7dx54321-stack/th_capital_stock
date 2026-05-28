#!/usr/bin/env python3
"""Build Phase 40 research review queue."""

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
from smr_research_review_queue import build_research_review_queue

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str | None = None) -> dict:
    return build_research_review_queue(conn, ticker=ticker)


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 40 Research Review Queue",
        "",
        "## Summary",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Queue Items"])
    for item in payload.get("items") or []:
        lines.append(f"- {item.get('ticker')} / {item.get('status')} / recommended: {item.get('recommended_review_action')}")
        lines.append(f"  Why not pending: {', '.join(item.get('why_not_pending') or [])}")
    lines.extend(["", "## Repair Rows"])
    for row in payload.get("repair_rows") or []:
        lines.append(f"- {row.get('ticker')} / {row.get('status')} / recommended: {row.get('recommended_action')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 40 research review queue")
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
