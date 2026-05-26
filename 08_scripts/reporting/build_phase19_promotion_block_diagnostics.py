#!/usr/bin/env python3
"""Build Phase 19 promotion block reason diagnostics."""

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
from smr_promotion_block_reason import build_ticker_block_diagnostics, build_watchlist_block_diagnostics, parse_tickers
from smr_registry import register_snapshot
from smr_runlog import log_run

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase19_promotion_block_diagnostics.py"


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", ticker: str | None = None, tickers: str | None = None) -> dict:
    if ticker:
        return build_ticker_block_diagnostics(conn, ticker, watchlist_id=watchlist)
    parsed = parse_tickers(tickers, watchlist_id=None) if tickers else None
    return build_watchlist_block_diagnostics(conn, watchlist_id=watchlist, tickers=parsed)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 19 promotion block diagnostics")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, watchlist=args.watchlist, ticker=args.ticker, tickers=args.tickers)
        entity_id = (args.ticker or args.tickers or args.watchlist)
        register_snapshot(
            conn,
            entity_type="phase19_promotion_block_diagnostics",
            entity_id=str(entity_id).upper() if args.ticker or args.tickers else args.watchlist,
            status="diagnosed",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase19 promotion block diagnostics built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
