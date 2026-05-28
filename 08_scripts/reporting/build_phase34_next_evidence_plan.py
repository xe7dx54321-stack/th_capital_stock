#!/usr/bin/env python3
"""Build Phase 34 next evidence acquisition plan."""

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
from smr_post_governance_evidence_state import build_next_evidence_plan

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None, tickers: str | None = None) -> dict[str, Any]:
    return build_next_evidence_plan(conn, ticker=ticker, tickers=tickers)


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 34 Next Evidence Plan",
        "",
        "## Summary",
        f"- Tickers checked: {summary.get('tickers_checked')}",
        f"- Evidence plan items: {summary.get('evidence_plan_items')}",
        f"- High priority plan items: {summary.get('high_priority_plan_items')}",
        f"- Repair queue items: {summary.get('repair_queue_items')}",
        "",
    ]
    for row in payload.get("ticker_results") or []:
        lines.extend([f"## {row.get('ticker')}", "| Type | Priority | Reason | Sources | Usage |", "|---|---|---|---|---|"])
        for item in row.get("plan_items") or []:
            lines.append(
                f"| {item.get('plan_type')} | {item.get('priority')} | {item.get('reason')} | "
                f"{', '.join(item.get('suggested_sources') or [])} | {item.get('allowed_usage_target')} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 34 next evidence plan")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, tickers=args.tickers)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
