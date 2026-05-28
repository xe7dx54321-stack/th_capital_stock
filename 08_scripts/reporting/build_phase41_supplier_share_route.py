#!/usr/bin/env python3
"""Build Phase 41 supplier share route report."""

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
from smr_supplier_share_route import build_supplier_share_route

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    return build_supplier_share_route(conn, ticker)


def render_markdown(payload: dict) -> str:
    body = payload.get("supplier_share_route") or {}
    lines = [
        f"# Phase 41 Supplier Share Route: {payload.get('ticker')}",
        "",
        f"- Status: {body.get('status')}",
        f"- Confirmed supplier share available: {body.get('confirmed_supplier_share_available')}",
        f"- Recommended usage: {body.get('recommended_usage')}",
        "",
        "## Route Rows",
    ]
    for row in body.get("route_rows") or []:
        lines.append(f"- {row.get('route_type')}: {row.get('availability')} / {row.get('allowed_usage')}")
    lines.extend(["", "## Do Not Do"])
    lines.extend(f"- {item}" for item in body.get("do_not_do") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 41 supplier share route")
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
