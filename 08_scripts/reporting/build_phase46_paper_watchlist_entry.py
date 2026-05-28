#!/usr/bin/env python3
"""Build Phase 46 paper watchlist entry."""

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
from smr_paper_watchlist_entry import build_paper_watchlist_entry, get_paper_watchlist_entry
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict:
    ticker = normalize_ticker(ticker)
    entry = get_paper_watchlist_entry(conn, ticker) or build_paper_watchlist_entry(conn, ticker)
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "paper_watchlist_entry": entry,
        "safety": {
            "watchlist_entry_is_pending": False,
            "watchlist_entry_is_paper_position": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    entry = payload.get("paper_watchlist_entry") or {}
    lines = [f"# Phase 46 Paper Watchlist Entry: {payload.get('ticker')}", "", "## Entry"]
    for key in (
        "watchlist_entry_id",
        "source_phase",
        "source_conclusion_status",
        "watchlist_status",
        "tracking_mode",
        "paper_watchlist_allowed",
        "pending_human_review_allowed",
        "paper_order_allowed",
        "real_trade_allowed",
    ):
        lines.append(f"- {key}: {entry.get(key)}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 46 paper watchlist entry")
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
