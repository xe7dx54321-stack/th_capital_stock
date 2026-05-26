#!/usr/bin/env python3
"""Build Phase 19 bear-case residual risk diagnostics."""

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
from smr_bear_case_response import decompose_bear_case_residual_risk
from smr_phase6_watchlists import load_watchlist_config
from smr_promotion_block_reason import latest_phase14_validation, latest_phase6_validation, row_for_ticker
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase19_bear_case_residual_risk.py"


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def ticker_payload(conn: sqlite3.Connection, ticker: str, *, watchlist: str = "ai_core") -> dict:
    phase14 = latest_phase14_validation(conn, watchlist)
    phase6 = latest_phase6_validation(conn)
    row = row_for_ticker(phase14, ticker)
    phase6_row = row_for_ticker(phase6, ticker, keys=("tickers", "ticker_results", "results"))
    bear = row.get("bear_case_gate") or ((phase6_row.get("bear_case_response") or {}).get("bear_case_gate") or {})
    if not bear and phase6_row.get("bear_case_response"):
        bear = phase6_row.get("bear_case_response")
    return decompose_bear_case_residual_risk(ticker.upper(), bear)


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", ticker: str | None = None, tickers: str | None = None) -> dict:
    if ticker:
        return ticker_payload(conn, ticker, watchlist=watchlist)
    rows = [ticker_payload(conn, item, watchlist=watchlist) for item in parse_tickers(tickers, watchlist)]
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "summary": {
            "tickers_checked": len(rows),
            "blocks_pending": sum(1 for row in rows if ((row.get("bear_case_residual_risk") or {}).get("blocks_pending"))),
            "reduced_size_allowed": sum(1 for row in rows if ((row.get("bear_case_residual_risk") or {}).get("allows_reduced_size_pending"))),
        },
        "ticker_results": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 19 bear-case residual risk diagnostics")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, watchlist=args.watchlist, ticker=args.ticker, tickers=args.tickers)
        register_snapshot(
            conn,
            entity_type="phase19_bear_case_residual_risk",
            entity_id=(args.ticker or args.tickers or args.watchlist),
            status="diagnosed",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase19 bear-case residual risk diagnostics built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
