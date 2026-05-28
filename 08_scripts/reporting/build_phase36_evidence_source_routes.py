#!/usr/bin/env python3
"""Build Phase 36 evidence source routes."""

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
from smr_evidence_source_route_planner import build_evidence_source_routes

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str) -> dict[str, Any]:
    return build_evidence_source_routes(conn, ticker)


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 36 Evidence Source Routes",
        "",
        f"## Ticker\n{payload.get('ticker')} / {payload.get('company_name')}",
        "",
    ]
    for row in payload.get("source_routes") or []:
        lines.extend([f"## {row.get('variable')}", "| Route | Priority | Expected Evidence | Usage | Limitations |", "|---|---|---|---|---|"])
        for route in row.get("source_routes") or []:
            lines.append(
                f"| {route.get('route_type')} | {route.get('priority')} | {route.get('expected_evidence_type')} | "
                f"{route.get('allowed_usage')} | {'; '.join(route.get('limitations') or [])} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 36 evidence source routes")
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
