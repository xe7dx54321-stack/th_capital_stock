#!/usr/bin/env python3
"""Build Phase 46 paper watchlist dashboard."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[0]
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase46_thesis_strength_score import build_payload as build_score
from smr_agents import DB_PATH
from smr_paper_watchlist_entry import list_paper_watchlist_entries
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TRACKING_FAMILY_STATUSES = {
    "active_tracking",
    "tracking_strengthened",
    "tracking_weakened",
    "tracking_needs_more_evidence",
}


def build_payload(conn: sqlite3.Connection) -> dict:
    entries = list_paper_watchlist_entries(conn)
    rows = []
    for entry in entries:
        score = build_score(entry.get("ticker")).get("thesis_strength_tracking") or {}
        rows.append(
            {
                "ticker": entry.get("ticker"),
                "watchlist_status": entry.get("watchlist_status"),
                "thesis_strength_bucket": score.get("thesis_strength_bucket"),
                "next_review": "weekly_or_on_new_evidence",
                "paper_order_allowed": False,
                "pending_allowed": False,
            }
        )
    current_statuses = [entry.get("watchlist_status") for entry in entries]
    return {
        "generated_at": now_ts(),
        "summary": {
            "watchlist_entries": len(entries),
            "active_tracking": sum(1 for status in current_statuses if status in TRACKING_FAMILY_STATUSES),
            "tracking_strengthened": current_statuses.count("tracking_strengthened"),
            "tracking_weakened": current_statuses.count("tracking_weakened"),
            "paper_orders_created": 0,
            "pending_created": 0,
            "real_trades_created": 0,
        },
        "ticker_rows": rows,
        "safety": {
            "dashboard_creates_pending": False,
            "dashboard_creates_order": False,
            "dashboard_creates_trade": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    lines = ["# Phase 46 Paper Watchlist Dashboard", "", "## Summary"]
    for key, value in (payload.get("summary") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Tickers"])
    for row in payload.get("ticker_rows") or []:
        lines.append(f"- {row.get('ticker')}: {row.get('watchlist_status')} / {row.get('thesis_strength_bucket')}")
        lines.append(f"  pending_allowed: {row.get('pending_allowed')}")
        lines.append(f"  paper_order_allowed: {row.get('paper_order_allowed')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 46 paper watchlist dashboard")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
