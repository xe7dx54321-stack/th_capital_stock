#!/usr/bin/env python3
"""Build Phase 47 periodic review state."""

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
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
from smr_paper_watchlist_periodic_review import build_periodic_review_state

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    state = build_periodic_review_state(conn, ticker)
    return {
        "generated_at": state.get("watchlist_status_before_review", ""),
        "ticker": state["ticker"],
        "periodic_review_state": state,
        "safety": {
            "review_due_is_pending": False,
            "review_strengthened_is_buy": False,
            "review_weakened_is_sell": False,
            "periodic_review_is_research_tracking": True,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
        },
    }


def render_markdown(payload: dict) -> str:
    state = payload.get("periodic_review_state") or {}
    lines = [
        f"# Phase 47 Periodic Review State: {payload.get('ticker')}",
        "",
        "## Review State",
        f"- review_status: {state.get('review_status')}",
        f"- watchlist_status_before_review: {state.get('watchlist_status_before_review')}",
        f"- review_cadence: {state.get('review_cadence')}",
        f"- last_reviewed_at: {state.get('last_reviewed_at')}",
        f"- next_review_reason: {state.get('next_review_reason')}",
        f"- pending_allowed: {state.get('pending_allowed')}",
        f"- paper_order_allowed: {state.get('paper_order_allowed')}",
        f"- real_trade_allowed: {state.get('real_trade_allowed')}",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 47 periodic review state")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
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
