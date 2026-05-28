#!/usr/bin/env python3
"""Build Phase 41 customer allocation route report."""

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
from smr_customer_allocation_route import build_customer_allocation_route

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    return build_customer_allocation_route(conn, ticker)


def render_markdown(payload: dict) -> str:
    body = payload.get("customer_allocation_route") or {}
    lines = [
        f"# Phase 41 Customer Allocation Route: {payload.get('ticker')}",
        "",
        f"- Status: {body.get('status')}",
        f"- Confirmed customer allocation available: {body.get('confirmed_customer_allocation_available')}",
        f"- Proxy allowed usage: {body.get('proxy_allowed_usage')}",
        "",
        "## Route Rows",
    ]
    for row in body.get("route_rows") or []:
        lines.append(f"- {row.get('route_type')}: {row.get('availability')} / {row.get('allowed_usage')}")
    lines.extend(["", "## Do Not Do"])
    lines.extend(f"- {item}" for item in body.get("do_not_do") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 41 customer allocation route")
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
