#!/usr/bin/env python3
"""Build Phase 40 specific evidence request report."""

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
from smr_specific_evidence_request import list_specific_evidence_requests
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str | None = None) -> dict:
    rows = list_specific_evidence_requests(conn, ticker=ticker)
    return {
        "generated_at": now_ts(),
        "ticker": str(ticker or "ALL").strip().upper(),
        "specific_evidence_requests": rows,
        "summary": {
            "requests_total": len(rows),
            "open_requests": sum(1 for row in rows if row.get("status") == "open"),
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed_true": 0,
        },
        "safety": {
            "request_builder_fetched_sources": False,
            "evidence_written": False,
            "pending_created": 0,
            "promotion_rules_relaxed": False,
        },
    }


def render_markdown(payload: dict) -> str:
    lines = [
        f"# Phase 40 Specific Evidence Requests: {payload.get('ticker')}",
        "",
        "## Requests",
    ]
    for row in payload.get("specific_evidence_requests") or []:
        lines.append(f"- {row.get('request_id')}: {row.get('evidence_type')} / {row.get('priority')}")
        lines.append(f"  Route: {row.get('allowed_source_route')}")
        lines.append(f"  Do not do: {', '.join(row.get('do_not_do') or [])}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 40 specific evidence requests")
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
