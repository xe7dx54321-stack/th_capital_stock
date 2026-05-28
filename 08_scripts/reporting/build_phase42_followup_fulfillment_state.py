#!/usr/bin/env python3
"""Build Phase 42 follow-up fulfillment state."""

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
from smr_followup_fulfillment_state import build_followup_fulfillment_state

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    return build_followup_fulfillment_state(conn, ticker)


def render_markdown(payload: dict) -> str:
    body = payload.get("followup_fulfillment_state") or {}
    lines = [f"# Phase 42 Follow-up Fulfillment State: {payload.get('ticker')}", "", "## Summary"]
    for key in ("requests_total", "fulfilled", "partial_fulfilled", "manual_input_required", "authorized_source_required", "scenario_only", "proxy_only"):
        lines.append(f"- {key}: {body.get(key)}")
    lines.extend(["", "## Requests"])
    for row in body.get("request_rows") or []:
        lines.append(f"- {row.get('request_type')}: {row.get('status')} / {row.get('allowed_usage')}")
        lines.append(f"  Next action: {row.get('next_action')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 42 follow-up fulfillment state")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default="300308.SZ")
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
